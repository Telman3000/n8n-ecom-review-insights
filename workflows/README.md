# n8n Workflow Documentation

## Review Analysis Workflow

This workflow automates the analysis of marketplace reviews and sends daily digests via Telegram.

### Workflow Steps

1. **Schedule Trigger** - Runs daily at a configured interval (default: every 24 hours)
2. **Health Check** - Verifies the analysis service is running
3. **Conditional Check** - Proceeds only if service is healthy, otherwise sends error alert
4. **Read Reviews** - Loads review data from CSV (can be replaced with Google Sheets node)
5. **Prepare Batch** - Formats reviews for API request
6. **Analyze Reviews** - Calls the analysis service with automatic retries (3 attempts)
7. **Aggregate Results** - Combines batch analysis results
8. **Process Summary** - Calculates overall statistics
9. **Format Digest** - Creates human-readable Telegram message
10. **Send Notification** - Sends digest to Telegram chat

### Error Handling

- Automatic retry on HTTP failures (3 attempts with 2s intervals)
- Service health check before processing
- Error alerts sent to Telegram if service is unavailable

### Configuration

Before importing the workflow, set these environment variables in n8n:

```bash
SERVICE_URL=http://service:8000
TELEGRAM_CHAT_ID=your_chat_id
```

You'll also need to configure Telegram credentials in n8n:
1. Go to Credentials → Add Credential → Telegram API
2. Create a bot via [@BotFather](https://t.me/botfather)
3. Add the bot token to n8n credentials

### Alternative: Google Sheets Integration

To read reviews from Google Sheets instead of CSV:

1. Replace the "Read Reviews CSV" node with "Google Sheets" node
2. Configure Google Sheets credentials in n8n
3. Set the spreadsheet URL and sheet name
4. Map columns: `id`, `product`, `rating`, `text`

### Importing the Workflow

1. Open n8n interface
2. Click "Workflows" → "Import from File"
3. Select `review_analysis_workflow.json`
4. Configure credentials and environment variables
5. Activate the workflow

### Sample Digest Output

```
📊 **Анализ отзывов завершен**

📈 **Всего отзывов:** 75

😊 **Настроения:**
• Позитивные: 45
• Нейтральные: 15
• Негативные: 15 (20.0%)

⚠️ **Приоритеты:**
• Критичные: 3
• Высокие: 5
• Средние: 12
• Низкие: 55

🏷️ **Топ темы:**
1. качество
2. доставка
3. цена
4. упаковка
5. размер

⚠️ **Частые жалобы:**
1. сломался через неделю
2. не соответствует описанию
3. упаковка повреждена

03.11.2026 17:00
```
