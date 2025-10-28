# 🚀 Quick Start Guide

Get up and running with the Kalshi Mention Market Research Tool in minutes!

## Prerequisites

- Python 3.8 or higher
- Kalshi API key (get one at [kalshi.com](https://kalshi.com))
- OpenAI API key (optional but recommended for AI features)

## Installation

### Option 1: Automated Installation (Recommended)

```bash
# Make the install script executable and run it
chmod +x install.sh
./install.sh
```

### Option 2: Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create cache directory
mkdir -p cache

# Copy environment template
cp env.example .env
```

## Configuration

1. **Edit the `.env` file** with your API keys:
   ```bash
   nano .env  # or use your preferred editor
   ```

2. **Required settings:**
   ```env
   KALSHI_API_KEY=your_kalshi_api_key_here
   ```

3. **Optional but recommended:**
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Test Your Setup

```bash
python test_setup.py
```

This will verify that all components are working correctly.

## Run the Application

```bash
python main.py
```

## Basic Usage

Once the application starts, you'll see a terminal interface. Here are some basic commands to get started:

### 1. Search for Markets
```
[kalshi-research] search Trump
```

### 2. View Trending Markets
```
[kalshi-research] trending
```

### 3. Analyze a Market
```
[kalshi-research] analyze MARKET_ID_123
```

### 4. Search News
```
[kalshi-research] news election 2024
```

### 5. Get Help
```
[kalshi-research] help
```

### 6. Exit
```
[kalshi-research] exit
```

## Example Workflow

1. **Start the application:**
   ```bash
   python main.py
   ```

2. **Search for mention markets:**
   ```
   [kalshi-research] search Biden
   ```

3. **Analyze a specific market:**
   ```
   [kalshi-research] analyze BIDEN_MENTION_2024
   ```

4. **View the AI analysis results** (if OpenAI is configured)

5. **Search for related news:**
   ```
   [kalshi-research] news Biden speech
   ```

## Troubleshooting

### Common Issues

**"Kalshi API not configured"**
- Make sure you've set `KALSHI_API_KEY` in your `.env` file
- Verify your API key is valid

**"AI analyzer not configured"**
- This is normal if you haven't set up OpenAI
- The tool will still work with basic analysis

**Import errors**
- Make sure you're in the virtual environment
- Try running `pip install -r requirements.txt` again

**Database errors**
- Check that the directory is writable
- Try deleting `kalshi_research.db` and running again

### Getting Help

- Run `python test_setup.py` to diagnose issues
- Check the full README.md for detailed documentation
- Look at the error messages for specific guidance

## Next Steps

Once you're up and running:

1. **Explore the features** - Try different search terms and commands
2. **Configure AI analysis** - Add your OpenAI API key for advanced features
3. **Customize settings** - Edit `config.yaml` for advanced configuration
4. **Set up data sources** - Configure Twitter, Reddit, or other APIs
5. **Automate research** - Use the data pipeline for systematic analysis

## Need More Help?

- 📖 Read the full [README.md](README.md) for comprehensive documentation
- 🔧 Check the [configuration options](README.md#configuration)
- 🐛 See the [troubleshooting section](README.md#troubleshooting)
- 💡 Explore the [advanced features](README.md#advanced-features)

Happy researching! 🎯



