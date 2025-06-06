# 🎯 TikTok Tracking Tag Updater

A Streamlit web application that automatically updates TikTok export files with DCM tracking tags and UTM parameters.

## 🚀 Live App
[**Launch App**](https://your-app-name.streamlit.app) *(Replace with your Streamlit Cloud URL)*

## ✨ Features

- **Smart Matching**: Automatically matches TikTok ads with DCM tags using Campaign Name, Ad Group Name, and Ad Name
- **URL Processing**: Prepends click trackers and adds missing UTM/TF parameters
- **Multi-file Support**: Upload multiple DCM tag files at once
- **Data Validation**: Validates required columns and provides helpful error messages
- **Processing Log**: Shows detailed results and unmatched rows
- **Easy Download**: Get updated Excel file ready for upload

## 📊 How It Works

### File Requirements

**TikTok Export File:**
- Excel file with 'Ads' sheet
- Headers in row 1
- Required columns: Campaign Name, Ad Group Name, Ad Name, Click URL, Impression tracking URL

**DCM Tag Files:**
- Excel files with headers in row 11
- Required columns: Campaign Name, Placement Name, Ad Name, Click Tracker, Impression Tracker

### Processing Logic

1. **Matching**: Finds matching rows using:
   - Campaign Name = Campaign Name
   - Ad Group Name (TikTok) = Placement Name (DCM)
   - Ad Name = Ad Name

2. **Click URL Updates**:
   - Prepends click tracker from DCM file
   - Adds missing UTM parameters: `utm_source=tiktok`, `utm_medium=paid`, `utm_campaign=<Campaign Name>`
   - Adds missing TF parameters: `tf_source=tiktok`, `tf_medium=paid_social`, `tf_campaign=<Campaign Name>`

3. **Impression URL Updates**:
   - Extracts impression tracking URL from quotes in DCM impression tracker field

## 🛠️ Local Development

### Prerequisites
- Python 3.8+
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/tiktok-tag-updater.git
cd tiktok-tag-updater

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 🚀 Deployment

### Streamlit Community Cloud (Free)

1. **Fork this repository** to your GitHub account
2. **Sign up** at [share.streamlit.io](https://share.streamlit.io)
3. **Deploy** by connecting your GitHub repository
4. **Share** your app URL with your team

### Other Deployment Options
- **Heroku**: Add `setup.sh` and `Procfile` for Heroku deployment
- **Docker**: Containerize for any cloud platform
- **AWS/GCP/Azure**: Deploy on major cloud providers

## 📁 Project Structure

```
tiktok-tag-updater/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # Documentation
├── .gitignore         # Git ignore file
├── .streamlit/        # Streamlit configuration
│   └── config.toml
└── assets/            # Screenshots and assets
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Bug Reports & Feature Requests

Please use the [GitHub Issues](https://github.com/yourusername/tiktok-tag-updater/issues) to report bugs or request features.

## ⭐ Support

If this tool helps you, please give it a star on GitHub!