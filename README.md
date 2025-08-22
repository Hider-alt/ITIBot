# ITI Bot

A Discord bot designed for the ITI Pascal-Comandini technical school that automatically monitors and notifies users about schedule changes and teacher variations.

## Overview

The bot automatically sends messages tagging class roles when a teacher from that class is added or removed from the schedule variations. It retrieves variation data from PDF files published on the [**ITI school website**](https://www.ispascalcomandini.it/variazioni-orario-istituto-tecnico-tecnologico/2017/09/15/), though PDF conversion may not always be perfectly accurate.

## Features

- **Automated Schedule Monitoring**: Checks for schedule changes every 15 minutes during school hours
- **Class Role Notifications**: Automatically tags relevant class roles when teachers are added/removed from variations  
- **PDF Processing**: Downloads and processes schedule variation PDFs from the school website
- **Analytics & Statistics**: Generates comprehensive statistics about schedule variations including:
  - Class-based variation counts and rankings
  - Teacher-based variation statistics  
  - Temporal analysis (yearly, monthly, weekly, hourly patterns)
  - Visual charts and graphs
- **Admin Commands**: 
  - Manual refresh of variations data
  - Message cleanup utilities
  - Statistics generation and export
- **MongoDB Integration**: Persistent data storage for historical analysis
- **Daily Alerts**: Notifications if no variations are detected for the next school day

## Technical Details

### Architecture
- Built with `discord.py` for Discord API integration
- Uses `MongoDB` with Motor async driver for data persistence
- PDF processing with `PyPDF2` and `pdfplumber` libraries
- Web scraping with `BeautifulSoup4` and `aiohttp`
- Data visualization with `matplotlib` and `pandas`
- OCR capabilities with `PaddleOCR` for complex PDF layouts

### Key Components
- **Variation API**: Scrapes and downloads PDF files from school website
- **PDF Utils**: Processes and extracts data from schedule PDFs
- **Database Layer**: MongoDB repositories for storing variations and configuration
- **Admin Cogs**: Discord slash commands for administration
- **Automated Loops**: Background tasks for continuous monitoring
- **Analytics System**: Statistical analysis and visualization tools

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables (Discord token, MongoDB connection, channel IDs, etc.)
4. Run the bot:
   ```bash
   python main.py
   ```

## Usage

The bot runs automatically once deployed. Admin users can use slash commands to:
- `/refresh_variazioni` - Manually refresh schedule variations
- `/invia_statistiche` - Send analytics to designated channels  
- `/genera_grafici` - Generate statistical charts
- `/clear` - Clean up messages in channels

## Notes

- Schedule monitoring is automatically paused during holidays (Christmas, summer break)
- PDF conversion accuracy may vary depending on the document format
- The bot is specifically designed for the ITI Pascal-Comandini school system
