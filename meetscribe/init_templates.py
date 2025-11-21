"""
Configuration templates for meetscribe init command.
"""


def get_init_template(provider: str) -> str:
    """
    Get YAML configuration template for a provider.

    Args:
        provider: Provider name

    Returns:
        YAML configuration template
    """
    templates = {
        'discord': DISCORD_TEMPLATE,
        'zoom': ZOOM_TEMPLATE,
        'meet': MEET_TEMPLATE,
        'proctap': PROCTAP_TEMPLATE,
        'obs': OBS_TEMPLATE,
    }

    return templates.get(provider, DEFAULT_TEMPLATE)


DISCORD_TEMPLATE = """# MeetScribe Discord Configuration

input:
  provider: discord
  params:
    bot_token: YOUR_DISCORD_BOT_TOKEN
    guild_id: YOUR_GUILD_ID
    channel_id: YOUR_CHANNEL_ID
    auto_join: false  # true = auto-join, false = notify only

convert:
  engine: whisper  # whisper, faster-whisper, gemini, passthrough
  params:
    model: whisper-1
    language: ja  # or 'auto'
    api_key: YOUR_OPENAI_API_KEY

llm:
  engine: notebooklm  # notebooklm, chatgpt, claude, gemini
  params:
    api_key: YOUR_NOTEBOOKLM_API_KEY
    # service_account_path: path/to/service-account.json

output:
  format: markdown  # markdown, json, pdf, docs, notebooklm
  params:
    output_dir: ./meetings

working_dir: ./meetings
cleanup_audio: false  # Delete raw audio after processing

metadata:
  project: my-project
  team: my-team
"""

ZOOM_TEMPLATE = """# MeetScribe Zoom Configuration

input:
  provider: zoom
  params:
    api_key: YOUR_ZOOM_API_KEY
    api_secret: YOUR_ZOOM_API_SECRET
    meeting_id: ZOOM_MEETING_ID

convert:
  engine: whisper
  params:
    model: whisper-1
    language: auto
    api_key: YOUR_OPENAI_API_KEY

llm:
  engine: chatgpt
  params:
    api_key: YOUR_OPENAI_API_KEY
    model: gpt-4

output:
  format: docs
  params:
    credentials_path: path/to/google-credentials.json
    folder_id: YOUR_GOOGLE_DRIVE_FOLDER_ID

working_dir: ./meetings
cleanup_audio: true
"""

MEET_TEMPLATE = """# MeetScribe Google Meet Configuration

input:
  provider: meet
  params:
    credentials_path: path/to/google-credentials.json
    drive_folder_id: YOUR_DRIVE_FOLDER_ID

convert:
  engine: gemini
  params:
    api_key: YOUR_GEMINI_API_KEY
    model: gemini-2.0-flash-exp

llm:
  engine: gemini
  params:
    api_key: YOUR_GEMINI_API_KEY
    model: gemini-2.0-flash-exp

output:
  format: markdown
  params:
    output_dir: ./meetings

working_dir: ./meetings
cleanup_audio: false
"""

PROCTAP_TEMPLATE = """# MeetScribe ProcTap Configuration (for confidential meetings)

input:
  provider: proctap
  params:
    process_name: zoom.exe  # or meet, teams, etc.
    audio_device: default

convert:
  engine: faster-whisper
  params:
    model_size: large-v3
    device: cuda  # or 'cpu'
    compute_type: float16

llm:
  engine: claude
  params:
    api_key: YOUR_CLAUDE_API_KEY
    model: claude-3-7-sonnet

output:
  format: json
  params:
    output_dir: ./meetings
    encrypt: true  # Encrypt output files

working_dir: ./meetings
cleanup_audio: true
"""

OBS_TEMPLATE = """# MeetScribe OBS Configuration

input:
  provider: obs
  params:
    recording_path: path/to/obs/recordings
    watch_folder: true

convert:
  engine: whisper
  params:
    model: whisper-1
    language: auto
    api_key: YOUR_OPENAI_API_KEY

llm:
  engine: notebooklm
  params:
    api_key: YOUR_NOTEBOOKLM_API_KEY

output:
  format: notebooklm
  params:
    share_url: true

working_dir: ./meetings
cleanup_audio: false
"""

DEFAULT_TEMPLATE = """# MeetScribe Configuration

input:
  provider: discord
  params:
    bot_token: YOUR_BOT_TOKEN

convert:
  engine: whisper
  params:
    api_key: YOUR_API_KEY

llm:
  engine: notebooklm
  params:
    api_key: YOUR_API_KEY

output:
  format: markdown
  params:
    output_dir: ./meetings

working_dir: ./meetings
cleanup_audio: false
"""
