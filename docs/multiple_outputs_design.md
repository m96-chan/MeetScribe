# 複数出力対応（直列・並列両対応） - 設計書 v2.0

## 概要

MeetScribeパイプラインで複数の出力形式を**直列または並列**で実行できるようにする機能拡張。

### ユースケース例
1. **並列実行**: Markdown + JSON + URL を同時生成（高速化）
2. **直列実行**: PDF生成 → Discord Webhook に PDF を添付して投稿（依存関係）
3. **混在実行**: グループ1（並列） → グループ2（並列）を順次実行

---

## 新しい要件

### 依存関係のあるユースケース

#### 例: PDF → Discord Webhook
```yaml
outputs:
  # グループ1: まずPDFを生成（直列実行）
  - format: pdf
    params:
      output_dir: ./meetings
    execution_group: 1

  # グループ2: PDFを使ってWebhookに投稿（直列実行）
  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/xxx/yyy"
      attach_pdf: true  # PDFを添付
    execution_group: 2
    depends_on: ["pdf"]
```

---

## 設計目標（更新版）

### 1. 複数出力のサポート
- 複数の出力形式を指定可能

### 2. 実行戦略の選択
- **並列実行（デフォルト）**: 独立した出力を同時実行
- **直列実行**: 依存関係のある出力を順次実行
- **グループ実行**: 実行グループで制御

### 3. 後方互換性
- 既存の単一出力形式をサポート継続

### 4. 依存関係の管理
- 出力間の依存関係を明示的に定義
- 依存する出力が失敗した場合、後続をスキップ

---

## 提案アーキテクチャ（更新版）

### 1. Configレイヤーの変更

#### 新しいデータモデル
```python
# meetscribe/core/config.py

@dataclass
class OutputConfig:
    """単一のOUTPUTレンダラーの設定"""
    format: str
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    on_error: str = "continue"  # "continue" または "stop"

    # NEW: 実行制御
    execution_group: int = 0  # 実行グループ番号（0=並列、1,2,3...=順次グループ）
    depends_on: List[str] = field(default_factory=list)  # 依存する出力形式名
    wait_for_group: bool = False  # グループ内でも直列実行するか

@dataclass
class PipelineConfig:
    """パイプライン全体の設定"""
    input: InputConfig
    convert: ConvertConfig
    llm: LLMConfig

    # 単一と複数の両方の出力をサポート
    output: Optional[OutputConfig] = None  # 後方互換性
    outputs: List[OutputConfig] = field(default_factory=list)  # NEW

    # NEW: 出力実行戦略
    output_execution_mode: str = "auto"  # "auto", "parallel", "serial"

    working_dir: Path = Path("./meetings")
    cleanup_audio: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_output_configs(self) -> List[OutputConfig]:
        """全出力設定を取得"""
        if self.outputs:
            return [cfg for cfg in self.outputs if cfg.enabled]
        elif self.output:
            return [self.output]
        else:
            raise ValueError("出力設定が見つかりません")

    def get_execution_groups(self) -> Dict[int, List[OutputConfig]]:
        """実行グループ別に出力を整理"""
        outputs = self.get_output_configs()
        groups = {}
        for output in outputs:
            group_num = output.execution_group
            if group_num not in groups:
                groups[group_num] = []
            groups[group_num].append(output)
        return groups
```

#### YAML パース処理
```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
    """辞書から設定を作成"""
    # ... 既存コード ...

    # NEW: 'output' と 'outputs' の両方に対応
    output_cfg = None
    outputs_cfg = []

    if 'outputs' in data:
        # 複数出力モード
        outputs_cfg = [
            OutputConfig(
                format=out['format'],
                params=out.get('params', {}),
                enabled=out.get('enabled', True),
                on_error=out.get('on_error', 'continue'),
                execution_group=out.get('execution_group', 0),  # NEW
                depends_on=out.get('depends_on', []),  # NEW
                wait_for_group=out.get('wait_for_group', False)  # NEW
            )
            for out in data['outputs']
        ]
    elif 'output' in data:
        # 単一出力モード（後方互換性）
        output_cfg = OutputConfig(
            format=data['output']['format'],
            params=data['output'].get('params', {})
        )

    output_execution_mode = data.get('output_execution_mode', 'auto')

    return cls(
        input=input_cfg,
        convert=convert_cfg,
        llm=llm_cfg,
        output=output_cfg,
        outputs=outputs_cfg,
        output_execution_mode=output_execution_mode,
        working_dir=working_dir,
        cleanup_audio=cleanup_audio,
        metadata=metadata
    )
```

---

### 2. Runnerレイヤーの変更

#### 直列・並列両対応の実行ロジック

```python
# meetscribe/core/runner.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any

class PipelineRunner:
    """MeetScribeパイプライン全体のオーケストレーション"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.input_provider: Optional[InputProvider] = None
        self.converter: Optional[ConvertProvider] = None
        self.llm_provider: Optional[LLMProvider] = None
        self.output_renderers: List[Dict[str, Any]] = []
        self.output_results_cache: Dict[str, Any] = {}  # NEW: 出力結果のキャッシュ

    def run(self, meeting_id: str) -> Dict[str, Any]:
        """パイプライン全体を実行"""
        logger.info(f"ミーティングのパイプライン開始: {meeting_id}")

        try:
            # Stage 1-3: INPUT → CONVERT → LLM
            audio_path = self.input_provider.record(meeting_id)
            transcript = self.converter.transcribe(audio_path, meeting_id)
            minutes = self.llm_provider.generate_minutes(transcript)

            # Stage 4: OUTPUT（実行戦略に応じて）
            logger.info(f"Stage 4/4: OUTPUT - 実行モード: {self.config.output_execution_mode}")
            output_results = self._execute_outputs(minutes, meeting_id)

            # クリーンアップ
            if self.config.cleanup_audio and audio_path.exists():
                audio_path.unlink()

            logger.info(
                f"パイプライン完了: {len(output_results['successful'])}成功, "
                f"{len(output_results['failed'])}失敗"
            )
            return output_results

        except Exception as e:
            logger.error(f"パイプライン失敗: {e}", exc_info=True)
            raise RuntimeError(f"パイプライン実行失敗: {e}") from e

    def _execute_outputs(self, minutes: Minutes, meeting_id: str) -> Dict[str, Any]:
        """
        出力実行戦略に応じて全出力を実行

        実行モード:
        - auto: execution_group を見て自動判定
        - parallel: 全て並列実行
        - serial: 全て直列実行
        """
        mode = self.config.output_execution_mode

        if mode == "parallel":
            # 強制並列実行
            return self._render_all_parallel(minutes, meeting_id)

        elif mode == "serial":
            # 強制直列実行
            return self._render_all_serial(minutes, meeting_id)

        else:  # mode == "auto"
            # execution_group を見て自動判定
            return self._render_all_auto(minutes, meeting_id)

    def _render_all_auto(self, minutes: Minutes, meeting_id: str) -> Dict[str, Any]:
        """
        execution_group に基づいて自動実行

        - グループ0: 並列実行（デフォルト）
        - グループ1,2,3...: 順次実行

        各グループ内は並列実行（wait_for_group=True なら直列）
        """
        execution_groups = self.config.get_execution_groups()

        results = {
            'successful': [],
            'failed': [],
            'skipped': [],
            'total': len(self.output_renderers)
        }

        # グループ番号順にソート
        sorted_groups = sorted(execution_groups.keys())

        for group_num in sorted_groups:
            group_outputs = execution_groups[group_num]
            logger.info(f"実行グループ {group_num}: {len(group_outputs)}個の出力を処理中")

            # グループ内の依存関係チェック
            group_outputs = self._filter_by_dependencies(group_outputs, results)

            if not group_outputs:
                logger.info(f"グループ {group_num}: スキップ（依存関係未満足）")
                continue

            # グループ内実行（並列 or 直列）
            if any(out.wait_for_group for out in group_outputs):
                # 直列実行
                group_results = self._render_group_serial(group_outputs, minutes, meeting_id)
            else:
                # 並列実行
                group_results = self._render_group_parallel(group_outputs, minutes, meeting_id)

            # 結果をマージ
            results['successful'].extend(group_results['successful'])
            results['failed'].extend(group_results['failed'])
            results['skipped'].extend(group_results.get('skipped', []))

            # クリティカルエラーチェック
            for failure in group_results['failed']:
                if failure.get('on_error') == 'stop':
                    logger.error(f"グループ {group_num} でクリティカルエラー発生")
                    raise RuntimeError(f"出力 {failure['format']} が失敗")

        return results

    def _filter_by_dependencies(
        self,
        outputs: List[OutputConfig],
        previous_results: Dict[str, Any]
    ) -> List[OutputConfig]:
        """
        依存関係をチェックして実行可能な出力のみ返す
        """
        successful_formats = {r['format'] for r in previous_results['successful']}
        filtered = []

        for output in outputs:
            if not output.depends_on:
                # 依存なし
                filtered.append(output)
            else:
                # 依存チェック
                if all(dep in successful_formats for dep in output.depends_on):
                    filtered.append(output)
                else:
                    logger.warning(
                        f"出力 {output.format} をスキップ: "
                        f"依存 {output.depends_on} が未完了"
                    )
                    previous_results['skipped'].append({
                        'format': output.format,
                        'reason': 'dependency_not_met',
                        'depends_on': output.depends_on
                    })

        return filtered

    def _render_group_parallel(
        self,
        outputs: List[OutputConfig],
        minutes: Minutes,
        meeting_id: str
    ) -> Dict[str, Any]:
        """グループ内の出力を並列実行"""
        results = {
            'successful': [],
            'failed': []
        }

        # ThreadPoolExecutor で並列実行
        with ThreadPoolExecutor(max_workers=len(outputs)) as executor:
            future_to_output = {}

            for output in outputs:
                renderer = self._get_renderer_by_format(output.format)
                future = executor.submit(
                    self._render_single_output,
                    renderer,
                    output,
                    minutes,
                    meeting_id
                )
                future_to_output[future] = output

            # 完了順に結果を収集
            for future in as_completed(future_to_output):
                output = future_to_output[future]

                try:
                    result = future.result()
                    results['successful'].append(result)
                    self.output_results_cache[result['format']] = result
                    logger.info(f"✓ {result['format']} 出力成功")

                except Exception as e:
                    logger.error(f"✗ {output.format} 出力失敗: {e}")
                    results['failed'].append({
                        'format': output.format,
                        'error': str(e),
                        'on_error': output.on_error
                    })

        return results

    def _render_group_serial(
        self,
        outputs: List[OutputConfig],
        minutes: Minutes,
        meeting_id: str
    ) -> Dict[str, Any]:
        """グループ内の出力を直列実行"""
        results = {
            'successful': [],
            'failed': []
        }

        for output in outputs:
            logger.info(f"直列実行: {output.format}")

            renderer = self._get_renderer_by_format(output.format)

            try:
                result = self._render_single_output(
                    renderer,
                    output,
                    minutes,
                    meeting_id
                )
                results['successful'].append(result)
                self.output_results_cache[result['format']] = result
                logger.info(f"✓ {result['format']} 出力成功")

            except Exception as e:
                logger.error(f"✗ {output.format} 出力失敗: {e}")
                results['failed'].append({
                    'format': output.format,
                    'error': str(e),
                    'on_error': output.on_error
                })

                # stop 時は即座に中断
                if output.on_error == 'stop':
                    raise

        return results

    def _render_all_parallel(self, minutes: Minutes, meeting_id: str) -> Dict[str, Any]:
        """全出力を並列実行（強制モード）"""
        outputs = self.config.get_output_configs()
        return self._render_group_parallel(outputs, minutes, meeting_id)

    def _render_all_serial(self, minutes: Minutes, meeting_id: str) -> Dict[str, Any]:
        """全出力を直列実行（強制モード）"""
        outputs = self.config.get_output_configs()
        return self._render_group_serial(outputs, minutes, meeting_id)

    def _render_single_output(
        self,
        renderer: OutputRenderer,
        output: OutputConfig,
        minutes: Minutes,
        meeting_id: str
    ) -> Dict[str, Any]:
        """単一の出力をレンダリング"""
        output_path = renderer.render(minutes, meeting_id)

        return {
            'format': output.format,
            'path': output_path,
            'renderer': renderer.__class__.__name__
        }

    def _get_renderer_by_format(self, format_name: str) -> OutputRenderer:
        """形式名からレンダラーを取得"""
        for renderer_cfg in self.output_renderers:
            if renderer_cfg['config'].format == format_name:
                return renderer_cfg['renderer']
        raise ValueError(f"レンダラーが見つかりません: {format_name}")
```

---

## 設定例

### 例1: 並列実行（デフォルト）
```yaml
outputs:
  - format: url
    params:
      save_metadata: true

  - format: markdown
    params:
      output_dir: ./meetings

  - format: json
    params:
      output_dir: ./meetings
```
全て `execution_group: 0`（デフォルト）なので並列実行。

### 例2: PDF → Discord Webhook（直列実行）
```yaml
outputs:
  # グループ1: PDF生成
  - format: pdf
    params:
      output_dir: ./meetings
    execution_group: 1

  # グループ2: Discord に投稿
  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/xxx/yyy"
      attach_pdf: true
    execution_group: 2
    depends_on: ["pdf"]
```
グループ1実行 → グループ2実行（順次）。

### 例3: 混在実行（並列 + 直列）
```yaml
outputs:
  # グループ0: 並列実行
  - format: url
    execution_group: 0
  - format: markdown
    execution_group: 0
  - format: json
    execution_group: 0

  # グループ1: PDF生成（直列）
  - format: pdf
    params:
      output_dir: ./meetings
    execution_group: 1

  # グループ2: Discord に投稿（直列）
  - format: discord_webhook
    params:
      webhook_url: "https://discord.com/api/webhooks/xxx/yyy"
    execution_group: 2
    depends_on: ["pdf"]
```
実行順序:
1. グループ0（URL, Markdown, JSON）を並列実行
2. グループ1（PDF）を実行
3. グループ2（Discord Webhook）を実行

### 例4: 強制並列実行
```yaml
output_execution_mode: parallel  # 強制並列

outputs:
  - format: pdf
    execution_group: 1  # 無視される
  - format: discord_webhook
    execution_group: 2  # 無視される
```
`execution_group` を無視して全て並列実行。

---

## 実装チェックリスト（更新版）

### Phase 1: Config Layer
- [ ] `OutputConfig` に `execution_group`, `depends_on`, `wait_for_group` を追加
- [ ] `PipelineConfig` に `output_execution_mode` を追加
- [ ] `get_execution_groups()` メソッドを実装
- [ ] YAML パーサーを更新

### Phase 2: Runner Layer
- [ ] `_execute_outputs()` メソッドを実装（戦略選択）
- [ ] `_render_all_auto()` メソッドを実装（自動判定）
- [ ] `_filter_by_dependencies()` メソッドを実装（依存関係チェック）
- [ ] `_render_group_parallel()` メソッドを実装（グループ並列実行）
- [ ] `_render_group_serial()` メソッドを実装（グループ直列実行）
- [ ] `_render_all_parallel()` メソッドを実装（強制並列）
- [ ] `_render_all_serial()` メソッドを実装（強制直列）
- [ ] `output_results_cache` を追加（依存関係用）

### Phase 3: Testing
- [ ] 単体テスト: `execution_group` によるグループ分け
- [ ] 単体テスト: `depends_on` による依存関係フィルタ
- [ ] 統合テスト: 並列実行
- [ ] 統合テスト: 直列実行
- [ ] 統合テスト: 混在実行（グループ0並列 → グループ1直列）
- [ ] E2Eテスト: PDF → Discord Webhook

---

## メリット

1. **柔軟性**: 並列・直列を自由に組み合わせ可能
2. **依存関係対応**: PDF生成後にWebhook投稿などが可能
3. **高速化**: 独立した出力は並列実行で高速化
4. **後方互換**: 既存設定はそのまま動作（デフォルトは並列）

---

## 所要時間見積もり（更新版）

- **Config Layer**: 2-3時間
- **Runner Layer（直列・並列対応）**: 6-8時間
- **依存関係管理**: 2-3時間
- **Testing**: 4-5時間
- **Documentation**: 1-2時間
- **合計**: **15-21時間**

---

## 結論

この設計により、MeetScribeは**並列実行と直列実行の両方をサポート**し、出力間の依存関係も管理できるようになります。

**PDF生成 → Discord Webhook に投稿**のようなユースケースに対応しつつ、デフォルトは並列実行で高速化を実現します。
