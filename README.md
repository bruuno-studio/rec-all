<div align="center">
  <img src="icon.svg" alt="rec-all Logo" width="120"/>
  <h1>rec-all</h1>
  <p><em>A Time Machine for the Everyday Digital Life</em></p>
</div>

---

> "In the Age of Fragmentation, Own Your Story. We live in a world saturated by fleeting moments—notifications that vanish, conversations lost to time, memories displaced by the next demand for attention. In this era of ephemera, there is a quiet rebellion: reclaiming not just the right to our data but to our existence as a continuous narrative."

## 🌟 Overview

rec-all is not just software; it is a revolution. It transforms your computer into a time machine, meticulously preserving every moment of your digital life—not as a voyeur, but as a loyal historian. Powered by advanced artificial intelligence, rec-all transforms raw data into an indexed, searchable experience.

## ✨ Features

- 🔄 **Continuous Screen Capture**: Automated, interval-based screen recording
- 🔍 **Advanced OCR**: Multi-language text recognition powered by EasyOCR
- 🤖 **AI Description**: Intelligent scene understanding and description generation
- 🔎 **Smart Search**: Search through both recognized text and AI-generated descriptions
- 📊 **Visual Timeline**: Chronological organization of your digital moments
- 🎥 **Time-lapse Creation**: Transform your captures into dynamic videos
- 📝 **Text Export**: Compile your digital memories into searchable documents
- 🔐 **Privacy-First**: All processing happens locally on your machine

## 🌍 Language Support
rec-all features OCR support for 8 languages:

Core Languages:
- English (en)
- Turkish (tr)

Additional Languages:
- French (fr)
- Spanish (es)
- German (de)
- Italian (it)
- Portuguese (pt)
- Dutch (nl)

Note: Language support may vary depending on your system configuration and successful model downloads.

## 💾 System Requirements

- Operating System: Windows 10/11
- Storage:
  - Minimum (English only, CPU version): 2.5 GB
  - Standard (All languages, CPU version): 5.5 GB
  - Full (All languages, CUDA version): 7.5 GB
- RAM: 8 GB minimum, 16 GB recommended
- Optional: NVIDIA GPU for CUDA acceleration

## 🚀 Installation

1. Clone the repository:

  git clone https://github.com/yourusername/rec-all.git

  cd rec-all

2. Run the setup script:
   
  setup.bat

3. Launch the application:
   
  launch.bat


## 🎯 Philosophy

rec-all is open source because freedom demands transparency. The sanctity of memory belongs to no corporation, no algorithmic overlord. When you use rec-all, you use a tool that is yours—not a product, not a service, but an extension of your own agency.

## 🤝 Contributing

rec-all is for everyone who refuses to be forgotten, for those who believe in the sanctity of their narrative. It is a canvas, a tool, a movement. Take it, use it, and shape it into something even greater.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 🛡️ Privacy & Security

To remember is to resist oblivion. But this act must be ethical. rec-all:
- Processes all data locally
- Never uploads your captures
- Stores data only on your machine
- Remains transparent through open source

## 🎨 Interface

- Modern, minimal design
- Dark mode for comfortable viewing
- Intuitive timeline navigation
- Smart search capabilities
- System tray integration

## 🔧 Technical Details

- Built with PyQt6 for robust GUI
- EasyOCR for advanced text recognition
- Microsoft's GIT-base model for AI description
- Local processing architecture
- Efficient data management

## 📚 Use Cases

- Personal Knowledge Management
- Digital Time Capsule
- Work Documentation
- Research Collection
- Learning Progress Tracking
- Project Documentation
- Digital Memory Archive

## ⚡ Performance

- Minimal system impact during capture
- Efficient background processing
- Smart resource management
- Optional CUDA acceleration

## ⚠️ Important Setup Notes

### Directory Selection
When choosing directories for rec-all, please consider:

- **Installation Directory**:
  - Choose a location with full read/write permissions
  - Avoid protected directories (e.g., `Program Files`)
  - Recommended: Create a dedicated folder in your user directory
    ```
    Good: C:\Users\YourName\rec-all
    Bad:  C:\Program Files\rec-all
    ```

- **Recording Directory**:
  - Select a directory with ample storage space
  - Ensure full read/write permissions
  - Avoid network drives or cloud-synced folders
  - Recommended locations:
    ```
    Good: D:\Recordings\rec-all
    Good: C:\Users\YourName\Documents\rec-all-recordings
    Bad:  C:\Windows\System32\recordings
    Bad:  C:\Program Files\recordings
    ```

### Permission Requirements
Insufficient permissions may cause:
- Failed screenshot captures
- OCR processing errors
- AI description generation failures
- Unable to save recordings
- Application crashes

To ensure optimal performance:
1. Run `setup.bat` as administrator during installation
2. Grant necessary permissions to both installation and recording directories
3. Consider creating a dedicated user account with appropriate permissions

## 🎁 Future Vision

We envision a world where every individual owns their digital shadow. Where data is not the currency of surveillance capitalism but the fabric of personal sovereignty. rec-all is our contribution to that world: a tool for those who wish to live deliberately, remembering deeply, and owning fully.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  <p><em>"Your moments matter. Even the quiet ones."</em></p>
</div>
