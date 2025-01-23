<p align="center">
  <a href="" rel="noopener">
    <img width=200px height=200px src="https://i.imgur.com/FxL5qM0.jpg" alt="Bot logo">
  </a>
</p>

<h3 align="center">NeuroChatting</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Platform](https://img.shields.io/badge/platform-Telegram-blue.svg)](https://telegram.org/)
[![GitHub Issues](https://img.shields.io/github/issues/atljh/NeuroChatting.svg)](https://github.com/atljh/NeuroChatting/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/atljh/NeuroChatting.svg)](https://github.com/atljh/NeuroChatting/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> 🤖 NeuroChatting is an AI-powered bot that uses Telethon sessions to interact with Telegram groups and respond intelligently to messages using ChatGPT.
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Features](#features)
- [How it works](#working)
- [Usage](#usage)
- [Getting Started](#getting_started)
- [Deploying your own bot](#deployment)
- [Security Guidelines](#security)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Authors](#authors)
- [Disclaimer](#disclaimer)
- [Acknowledgments](#acknowledgement)

---

## 🧐 About <a name = "about"></a>

NeuroChatting is a Python-based Telegram bot designed to bring the power of AI into group conversations. By leveraging Telethon for session management and OpenAI's ChatGPT for generating responses, this bot offers seamless and intelligent interaction in Telegram groups.

---

## 🌟 Features <a name = "features"></a>

- 🌐 Intelligent group interaction using ChatGPT responses.
- 🌀 Support for multiple Telegram accounts through `.session` and `.json` files.
- ⚡ Customizable response tone and behavior.
- 🔄 Automatic switching of accounts after a set number of messages.
- 🛠️ Reaction modes: keyword-based or interval-based.
- 📈 Scalable with Docker for easy deployment.

---

## 💭 How it works <a name = "working"></a>

1. **Telethon Sessions**: The bot uses `.session` and `.json` files to authenticate and manage Telegram accounts.
2. **Message Listening**: The bot listens to incoming messages in Telegram groups.
3. **AI Responses**: Upon receiving a message, it sends the content to the OpenAI API (ChatGPT) and generates an intelligent response.
4. **Message Sending**: The bot replies directly in the group, ensuring smooth and real-time interaction.

---

## 🎈 Usage <a name = "usage"></a>

To use the bot:
1. Add the bot to a Telegram group.
2. Start a conversation, and the bot will reply to messages intelligently.

### Example:

**Group Message**:  
> Can anyone explain how to use AI in Python?

**Bot Reply**:  
> Sure! AI in Python can be implemented using libraries like TensorFlow, PyTorch, or pre-built APIs like OpenAI's GPT. Let me know if you'd like a detailed example!

---

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

3. Create a `config.yaml` file based on `config-sample.yaml` and add your credentials.

4. Run the bot:

    ```bash
    python main.py
    ```

---

## 🚀 Deploying your own bot <a name = "deployment"></a>

You can deploy the bot on a live server using platforms like Heroku, AWS, or Docker.

### Using Docker:

1. Build the Docker image:

    ```bash
    docker build -t neurochatting .
    ```

2. Run the container:

    ```bash
    docker run -d --env-file .env neurochatting
    ```

---

## 🔒 Security Guidelines <a name = "security"></a>

- Avoid using your personal Telegram accounts for testing. Create separate accounts.
- Use proxies or VPNs to protect your IP if deploying in sensitive environments.
- Regularly update the bot and its dependencies to minimize vulnerabilities.
- Store sensitive data (API keys, session files) in secure locations or encrypted files.

---

## ❓ FAQ <a name = "faq"></a>

### 1. Can I use this bot with my personal Telegram account?  
It is recommended to create separate accounts for testing and deployment to avoid risks of bans.

### 2. How can I add more accounts to the bot?  
Simply place `.session` or `.json` files in the `accounts/` directory, and the bot will automatically detect them.

### 3. Why am I getting account bans?  
Excessive automation or aggressive actions might trigger Telegram's anti-spam measures. Follow the Security Guidelines section.

---


## 📸 Screenshots <a name = "screenshots"></a>

 ![Group Message](https://i.imgur.com/fsYP4HC.png)
---


## 🛤️ Roadmap <a name = "roadmap"></a>

- [x] Support for multiple accounts
- [x] Integration with ChatGPT API
- [ ] Web-based control panel for managing the bot
- [ ] Enhanced response customization options
- [ ] Multi-language support

---

## 🤝 Contributing <a name = "contributing"></a>

We welcome contributions to NeuroChatting! To contribute:

1. Fork the repository.  
2. Create a new branch: `git checkout -b feature/your-feature-name`.  
3. Commit your changes: `git commit -m 'Add your feature'`.  
4. Push to the branch: `git push origin feature/your-feature-name`.  
5. Submit a pull request.

Please check our [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

---

## ✍️ Authors <a name = "authors"></a>

- **@atljh** - Creator & Maintainer

---

## ⚠️ Disclaimer <a name = "disclaimer"></a>

NeuroChatting is intended for educational and informational purposes only. 

- Use this bot responsibly and ensure compliance with Telegram's [Terms of Service](https://telegram.org/tos) and OpenAI's [Usage Policies](https://platform.openai.com/docs/usage-policies).
- The creator is not liable for any misuse or potential violations resulting from improper use of this software.
- Be aware that excessive or automated interactions on Telegram could lead to account restrictions or bans. Use caution when managing multiple sessions or performing high-frequency actions.

---

## 🎉 Acknowledgments <a name = "acknowledgement"></a>

- OpenAI for their amazing GPT API  
- Telethon for their robust Telegram API wrapper  
- Inspiration from various Telegram automation projects