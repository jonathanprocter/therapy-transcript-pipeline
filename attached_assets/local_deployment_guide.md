# Therapy Transcript Processor - Local Deployment Guide

This guide provides detailed instructions for deploying the Therapy Transcript Processor application on your own server or cloud platform.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Access to a server or cloud platform that can host Python applications
- API keys for Dropbox, OpenAI/Claude/Gemini, and Notion

## Local Setup and Testing

1. **Clone or download the application code**
   - Ensure you have the complete `full_integration_app` directory

2. **Create a virtual environment**
   ```bash
   cd full_integration_app
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys**
   - Create a `.env` file in the root directory with the following content:
   ```
   DROPBOX_TOKEN=your_dropbox_token
   OPENAI_KEY=your_openai_key
   CLAUDE_KEY=your_claude_key
   GEMINI_KEY=your_gemini_key
   NOTION_KEY=your_notion_key
   NOTION_PARENT_ID=your_notion_parent_page_id
   DROPBOX_FOLDER=/apps/otter
   ```

5. **Run the application locally**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open a browser and navigate to `http://localhost:3000`
   - Log in with the password: `5786`

## Deployment Options

### Option 1: Deploy on Heroku

1. **Create a Heroku account and install the Heroku CLI**
   - Sign up at [heroku.com](https://heroku.com)
   - Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

2. **Login to Heroku and create a new app**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Set environment variables**
   ```bash
   heroku config:set DROPBOX_TOKEN=your_dropbox_token
   heroku config:set OPENAI_KEY=your_openai_key
   heroku config:set CLAUDE_KEY=your_claude_key
   heroku config:set GEMINI_KEY=your_gemini_key
   heroku config:set NOTION_KEY=your_notion_key
   heroku config:set NOTION_PARENT_ID=your_notion_parent_page_id
   heroku config:set DROPBOX_FOLDER=/apps/otter
   ```

4. **Deploy the application**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku master
   ```

5. **Open the application**
   ```bash
   heroku open
   ```

### Option 2: Deploy on AWS Elastic Beanstalk

1. **Install the AWS CLI and EB CLI**
   - Follow the [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
   - Follow the [EB CLI installation guide](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html)

2. **Configure AWS credentials**
   ```bash
   aws configure
   ```

3. **Initialize EB application**
   ```bash
   eb init -p python-3.8 therapy-transcript-processor
   ```

4. **Create an environment**
   ```bash
   eb create therapy-transcript-env
   ```

5. **Set environment variables**
   - Go to the AWS Elastic Beanstalk Console
   - Navigate to your environment
   - Go to Configuration > Software
   - Add environment variables for all API keys

6. **Deploy the application**
   ```bash
   eb deploy
   ```

7. **Open the application**
   ```bash
   eb open
   ```

### Option 3: Deploy on DigitalOcean App Platform

1. **Create a DigitalOcean account**
   - Sign up at [digitalocean.com](https://digitalocean.com)

2. **Create a new app**
   - Go to the App Platform section
   - Click "Create App"
   - Connect your GitHub repository or upload your code

3. **Configure the app**
   - Select Python as the environment
   - Set the run command to `gunicorn wsgi:application`
   - Add environment variables for all API keys

4. **Deploy the app**
   - Click "Deploy to Production"

5. **Access your app**
   - Use the URL provided by DigitalOcean

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Verify all API keys are correctly configured in environment variables
   - Check that the Notion parent page ID is correct and accessible
   - Ensure your Dropbox token has the necessary permissions

2. **File Processing Issues**
   - Ensure PDF files are in a readable format and under 16MB
   - Check that filenames follow expected patterns for client name extraction
   - Verify the Dropbox folder path is correct (`/apps/otter` by default)

3. **Notion Database Issues**
   - Confirm the parent page exists and is accessible to the integration
   - Check that your Notion API key has the necessary permissions
   - Verify that the integration has been added to the parent page

4. **Application Errors**
   - Check the application logs for detailed error information
   - Restart the application if it becomes unresponsive
   - Clear browser cache and cookies if the web interface behaves unexpectedly

### Checking Logs

- **Heroku**: `heroku logs --tail`
- **AWS Elastic Beanstalk**: `eb logs`
- **DigitalOcean**: View logs in the App Platform console

## Support

For additional support or questions, please contact the developer.

## Security Considerations

- Always use HTTPS in production
- Keep API keys secure and never commit them to version control
- Regularly rotate API keys for better security
- Implement proper backup procedures for your data
