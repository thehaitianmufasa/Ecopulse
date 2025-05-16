# EcoNews - Financial News Aggregator

A modern, Gen-Z focused financial news aggregator built with Flask, featuring real-time market updates and categorized news feeds.

## Features

- 📈 Real-time market updates
- 📰 Categorized news sections (Markets, Stocks, Crypto, Real Estate, Tech)
- 🎨 Modern, responsive UI with glassmorphism design
- 🌓 Dark/Light theme toggle
- 📱 Mobile-friendly interface
- 🔍 Smart news filtering and categorization
- ⚡ Real-time API integration

## Tech Stack

- Backend: Python/Flask
- Frontend: HTML5, CSS3, JavaScript
- News Data: NewsAPI
- Deployment: Render

## Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/thehaitianmufasa/Ecopulse.git
cd Ecopulse
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory and add:
```
NEWS_API_KEY=your_api_key_here
FLASK_ENV=development
```

5. Run the application:
```bash
python main.py
```

Visit `http://localhost:5000` in your browser.

## API Endpoints

- `/` - Homepage with trending news
- `/markets` - Financial markets news
- `/stocks` - Stock market updates
- `/crypto` - Cryptocurrency news
- `/real-estate` - Real estate market news
- `/tech` - Technology sector news

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NewsAPI for providing real-time news data
- Flask framework and its community
- Modern UI/UX inspiration from current Gen-Z focused applications