<p align="center">
  <a href="" rel="noopener">
    <img width=200px height=200px src="https://i.imgur.com/FxL5qM0.jpg" alt="Bot logo">
  </a>
</p>

<h3 align="center">NeuroChatting</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Platform](https://img.shields.io/badge/platform-Telegram-blue.svg)](https://telegram.org/)
[![GitHub Issues](https://img.shields.io/github/issues/username/NeuroChatting.svg)](https://github.com/username/NeuroChatting/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/username/NeuroChatting.svg)](https://github.com/username/NeuroChatting/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> 🤖 NeuroChatting is an AI-powered bot that uses Telethon sessions to interact with Telegram groups and respond intelligently to messages using ChatGPT.
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Demo / Working](#demo)
- [How it works](#working)
- [Usage](#usage)
- [Getting Started](#getting_started)
- [Deploying your own bot](#deployment)
- [Built Using](#built_using)
- [TODO](../TODO.md)
- [Contributing](../CONTRIBUTING.md)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>

NeuroChatting is a Python-based Telegram bot designed to bring the power of AI into group conversations. By leveraging Telethon for session management and OpenAI's ChatGPT for generating responses, this bot offers seamless and intelligent interaction in Telegram groups.

Key Features:
- Uses `.session` and `.json` Telethon session files for account management.
- Automatically responds to group messages with AI-powered answers.
- Handles multiple sessions and adapts responses to group conversations.

## 🎥 Demo / Working <a name = "demo"></a>

![Working](https://media.giphy.com/media/20NLMBm0BkUOwNljwv/giphy.gif)

## 💭 How it works <a name = "working"></a>

1. **Telethon Sessions**: The bot uses `.session` and `.json` files to authenticate and manage Telegram accounts.
2. **Message Listening**: The bot listens to incoming messages in Telegram groups.
3. **AI Responses**: Upon receiving a message, it sends the content to the OpenAI API (ChatGPT) and generates an intelligent response.
4. **Message Sending**: The bot replies directly in the group, ensuring smooth and real-time interaction.

## 🎈 Usage <a name = "usage"></a>

To use the bot:
1. Add the bot to a Telegram group.
2. Start a conversation, and the bot will reply to messages intelligently.

### Example:

Group Message:
> Can anyone explain how to use AI in Python?

Bot Reply:
> Sure! AI in Python can be implemented using libraries like TensorFlow, PyTorch, or pre-built APIs like OpenAI's GPT. Let me know if you'd like a detailed example!

## 🏁 Getting Started <a name = "getting_started"></a>

Follow these steps to get the bot running locally.

### Prerequisites

- Python 3.9 or higher
- A Telegram account
- OpenAI API key

### Installing

1. Clone this repository:

   ```bash
   git clone https://github.com/atljh/NeuroChatting.git
   cd NeuroChatting 
   ```
2. Install the dependencies:

    ```bash
    pip install poetry
    poetry install
    ```

3. Create a config.yaml file based on config-sample.yaml and add your credentials

Run the bot:

    python bot.py

🚀 Deploying your own bot <a name = "deployment"></a>

You can deploy the bot on a live server using platforms like Heroku, AWS, or Docker.
Using Docker:

    Build the Docker image:

docker build -t neurochatting .

Run the container:

    docker run -d --env-file .env neurochatting

⛏️ Built Using <a name = "built_using"></a>

    Telethon - Telegram API Library
    OpenAI API - AI for intelligent responses
    Python - Programming Language

✍️ Authors <a name = "authors"></a>

    @atljh - Creator & Maintainer

🎉 Acknowledgments <a name = "acknowledgement"></a>

    OpenAI for their amazing GPT API
    Telethon for their robust Telegram API wrapper
    Inspiration from various Telegram automation projects