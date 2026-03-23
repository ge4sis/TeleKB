# 🚀 TeleKB (Telegram Knowledge Base)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Gemini API](https://img.shields.io/badge/AI-Gemini-orange.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**TeleKB** is a powerful local GUI application designed to transform your Telegram subscriptions into a structured, searchable, and translated personal knowledge base. It fetches messages from channels and groups, identifies foreign languages, and uses **Google Gemini AI** to provide high-quality Korean translations—all saved as neat Markdown files.

---

## ✨ Key Features

*   **🔄 Multi-device Synchronization (New!)**: Seamlessly sync your channel list and collection progress across multiple devices using your GitHub-managed output directory. No more duplicate messages or missing history!
*   **📂 Intelligent Markdown Export**: Saves messages in a clean `YYYY-MM/channel_YYYYMMDD.md` structure. Preserves original formatting, hyperlinks, and media links.
*   **🤖 AI-Powered Translation**: Automatically detects non-Korean text and provides context-aware translations via **Google Gemini**.
*   **🖼️ Media Archiving**: Automatically downloads images from messages and links them directly within your Markdown files.
*   **🛠️ Simple Channel Management**: A user-friendly GUI to add, remove, and manage your source channels without touching the database.
*   **🔐 Privacy First**: Your Telegram session and database stay local. Your data, your rules.

---

## 📡 Multi-device Sync: How it Works

TeleKB now includes a robust synchronization system designed for users who manage their files via **GitHub**, **Dropbox**, or **Google Drive**.

1.  **Shared State**: A `sync_state.json` file is automatically created in your selected **Output Directory**.
2.  **Seamless Continuity**: When you run TeleKB on a new machine, it reads this JSON file to automatically add your channels and resume from the exact last message collected on other devices.
3.  **Conflict-Free**: The local database handles binary storage, while the JSON ensures text-based, Git-friendly synchronization of metadata.

---

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/TeleKB.git
    cd TeleKB
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r TeleKB/requirements.txt
    ```

## ⚙️ Configuration

1.  Create a `.env` file in the root directory (refer to `.env.template`).
2.  Add your credentials:
    ```ini
    API_ID=12345678
    API_HASH=your_telegram_hash
    GEMINI_API_KEY=your_gemini_key
    ```
    *   *Get Telegram keys at [my.telegram.org](https://my.telegram.org)*
    *   *Get Gemini keys at [Google AI Studio](https://aistudio.google.com/)*

---

## 🚀 Usage

1.  **Start the App**: `python main.py`
2.  **Select Output**: Choose the folder you sync with GitHub/Cloud storage.
3.  **Manage Channels**: Add your favorite Telegram channels.
4.  **Run Collection**: Click the button and watch your knowledge base grow!

---

⭐ **If you find this useful, please [give it a star](https://github.com/ge4sis/TeleKB)! It helps our project grow.**

---

# 🇰🇷 TeleKB (Telegram Knowledge Base) - 한국어 가이드

**TeleKB**는 텔레그램 구독 정보를 체계적인 지식 베이스로 변환해주는 로컬 GUI 도구입니다. 복잡한 채널 메시지를 모으고, 외국어는 **Google Gemini AI**를 통해 한국어로 번역하여 깔끔한 Markdown 파일로 저장합니다.

## ✨ 주요 기능

*   **🔄 기기 간 동기화 (최신!)**: GitHub 등으로 관리하는 출력 폴더를 통해 채널 목록과 수집 시점을 여러 기기에서 완벽하게 공유합니다. 
*   **📂 스마트 Markdown 내보내기**: `YYYY-MM/채널명_YYYYMMDD.md` 구조로 깔끔하게 저장하며, 원본 링크와 서식을 그대로 보존합니다.
*   **🤖 AI 자동 번역**: 한국어가 아닌 메시지만 골라내어 **Google Gemini**가 자연스러운 한국어로 번역합니다.
*   **🖼️ 이미지 아카이빙**: 메시지 내 이미지를 자동 다운로드하고 Markdown 문서 내에 로컬 링크로 삽입합니다.
*   **🛠️ 직관적인 GUI**: 복잡한 설정 없이 버튼 클릭만으로 채널을 관리하고 수집을 실행할 수 있습니다.

## 📡 동기화 기능 활용법

GitHub와 같은 클라우드 동기화 서비스를 사용 중이라면 더욱 강력하게 활용할 수 있습니다.

1. **상태 공유**: 설정된 출력 폴더에 `sync_state.json` 파일이 생성됩니다.
2. **이어하기**: 기기 A에서 수집한 후 Push하면, 기기 B에서 Pull 후 실행 시 **별도 설정 없이** 이어서 수집을 시작합니다.
3. **병합 최적화**: 텍스트 기반의 JSON 파일로 연동되므로 Git 충돌 걱정 없이 안전하게 동기화됩니다.

## 🚀 시작하기

1. `main.py` 실행 후 **Output Directory**를 GitHub 동기화 폴더로 지정하세요.
2. **Channel Management**에서 원하는 채널을 추가하세요.
3. **Run Collection**을 누르면 수집이 시작됩니다.

---

## 📄 License
MIT License. 상세 내용은 [LICENSE](LICENSE) 파일을 확인하세요.

---

🌟 **이 프로젝트가 도움이 되었다면 [여기에서 Star](https://github.com/ge4sis/TeleKB)를 눌러 응원해 주세요! 프로젝트가 지속되는 데 큰 힘이 됩니다.**
