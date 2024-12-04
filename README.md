<div align="center">
  <img src="icon.svg" alt="rec-all Logo" width="120"/>
  <h1>rec-all</h1>
  <p><em>A Time Machine for the Everyday</em></p>
</div>

<div align="center">
    <img src="https://github.com/user-attachments/assets/ac18baaf-e583-4355-85cd-07a4e934d640" alt="rec-all demo" />
</div>
---

> "In the Age of Fragmentation, Own Your Story. We live in a world saturated by fleeting moments—notifications that vanish, conversations lost to time, memories displaced by the next demand for attention. In this era of ephemera, there is a quiet rebellion: reclaiming not just the right to our data but to our existence as a continuous narrative."

## 🌟 Overview

rec-all is not just software; it is a revolution. It transforms your computer into a time machine, meticulously preserving every moment of your digital life—not as a voyeur, but as a loyal historian. Powered by advanced artificial intelligence, rec-all transforms raw data into an indexed, searchable experience.

![rec-all_screenshot](https://github.com/user-attachments/assets/8c1736ac-f38d-43f7-8927-68a1e09c91b4)


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

### Method 1: Direct Download
1. Download the latest release from [GitHub Releases](https://github.com/bruuno-studio/rec-all/releases)
2. Extract the ZIP file to your desired location
3. Right-click `setup.bat` and select "Run as administrator"
4. After setup completes, use the `rec-all` shortcut in the installation folder

### Method 2: Using Git
1. Clone the repository:
```
  git clone https://github.com/bruuno-studio/rec-all.git
```
2. Open the directory:
```
  cd rec-all
```
3. Run the setup script:
```
  setup.bat
```
4. Launch the application:
   
  rec-all shortcut

  ## 🚀 Quick Start

1. **First Launch**
   - Choose recording directory
   - Select capture interval
   - Enable desired features (OCR/AI)

2. **Basic Usage**
   - Start/Stop recording from system tray
   - View captures in timeline
   - Search through content
   - Create time-lapse videos
   - Export text summaries

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

### ⚠️ Permission Requirements
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

## 💡 Tips & Best Practices

- **Storage Management**
  - Regular cleanup of old captures
  - Use external drive for long-term storage

- **Performance Optimization**
  - Use CUDA acceleration when available

- **Privacy Considerations**
  - Pause recording during sensitive tasks
  - Regular review of captured content
 
## 🔧 Troubleshooting

### Common Issues

**Application Won't Start**
- Ensure Python is properly installed
- Run setup.bat as administrator
- Check Windows Event Viewer for errors

**Black Screenshots**
- Disable hardware acceleration in your browser
- Update graphics drivers
- Check Windows display settings

**OCR Not Working**
- Ensure language models are downloaded
- Check internet connection during setup
- Verify sufficient disk space

**High CPU Usage**
- Adjust capture interval
- Disable AI features if not needed
- Close unnecessary applications

## ❓ FAQ

**Q: How much disk space does rec-all use?**
  A: Storage usage varies based on:
  - Screen resolution
  - Capture interval
  - Enabled features (OCR/AI)
  For example, at 1080p with 5-second intervals, expect roughly 70-200MB per hour.

**Q: Does rec-all work with multiple monitors?**
  A: No, rec-all only captures the main monitor.

**Q: Can I change the capture interval?**
  A: Yes, you can adjust the interval in the settings menu (minimum: 1 second).

**Q: Does rec-all require internet?**
  A: Internet is only required during initial setup for downloading language models and AI components. After setup, rec-all works completely offline.

**Q: Where is my data stored?**
  A: All captures are stored locally in your chosen recording directory.

**Q: Will rec-all start automatically with Windows?**
  A: No, you need to manually start rec-all each time you want to use it.

**Q: Can I use rec-all without the AI features?**
  A: Yes, AI features are optional. You can use rec-all with just basic screen capture, or enable OCR without AI descriptions.

**Q: What happens if my computer crashes during recording?**
  A: rec-all saves each capture independently, so you'll only lose the most recent unsaved capture. Previous captures remain safe.

## 🎁 Future Vision

We envision a world where every individual owns their digital shadow. Where data is not the currency of surveillance capitalism but the fabric of personal sovereignty. rec-all is our contribution to that world: a tool for those who wish to live deliberately, remembering deeply, and owning fully.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  <p><em>"Your moments matter. Even the quiet ones."</em></p>
</div>
