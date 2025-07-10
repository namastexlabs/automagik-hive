# Knowledge Management Guide for PagBank Team 📋

## For Management: How to Update Knowledge Base

### ✅ **Current Status**: Working and Active
- Knowledge base has **651 entries** loaded successfully
- CSV hot reload manager is **ACTIVE** (integrated in main system)
- System checks for changes **every 60 seconds**

---

## 🎯 **Simple Workflow (KISS)**

### Step 1: Edit the CSV File
1. Open `knowledge/pagbank_knowledge.csv` in **Excel** or **Google Sheets**
2. Add new rows or edit existing content
3. **Save the file**

### Step 2: That's It! 
- System automatically detects changes within 60 seconds
- Knowledge base reloads automatically 
- **No restart needed**
- **No technical intervention required**

---

## 📊 **CSV File Structure**

Each row should have these columns:
- **conteudo**: The knowledge content (what customers need to know)
- **area**: Product area (`cartoes`, `conta_digital`, `investimentos`, `credito`, `seguros`)
- **tipo_produto**: Specific product type (`pix`, `cartao_credito`, `cdb`, etc.)
- **tipo_informacao**: Info type (`beneficios`, `como_solicitar`, `taxas`, etc.)
- **nivel_complexidade**: Complexity (`basico`, `intermediario`, `avancado`)
- **publico_alvo**: Target audience (`pessoa_fisica`, `pessoa_juridica`, etc.)
- **palavras_chave**: Keywords for search
- **atualizado_em**: Update date (YYYY-MM format)

---

## 🔄 **Cloud Sync Options**

### Option A: Dropbox/OneDrive Sync
1. Save CSV file to synchronized folder
2. Changes automatically sync to server
3. System detects and applies changes

### Option B: Google Sheets (Future)
1. Edit in Google Sheets 
2. Export/sync to CSV automatically
3. System picks up changes

### Option C: Manual Upload
1. Edit CSV locally
2. Upload to server (replace existing file)
3. System detects change automatically

---

## 📈 **Example: Adding New Knowledge**

### Scenario: New PIX feature launched

**Add this row to CSV**:
```csv
"PIX Agendado permite programar transferências para até 60 dias no futuro. Disponível no app PagBank gratuitamente.",conta_digital,pix,beneficios,basico,pessoa_fisica,"pix agendado transferencia futuro 60 dias app pagbank gratuito",2025-07
```

**What happens**:
1. Save CSV file ✅
2. Within 60 seconds, system detects change 🔄
3. Knowledge base reloads automatically ⚡
4. Agents immediately know about new feature 🤖
5. Customers get updated information instantly 📞

---

## 🛠️ **Monitoring & Troubleshooting**

### Check System Status
```bash
# Check if manager is running
uv run python knowledge/csv_hot_reload.py --status

# Force immediate reload (if needed)
uv run python knowledge/csv_hot_reload.py --force-reload
```

### System Status Indicators
- ✅ **"CSV hot reload manager: ACTIVE"** in startup logs
- ✅ **"Knowledge base reloaded successfully"** when changes detected
- ✅ **Search validation working** after each reload

### If Something Goes Wrong
1. **Check CSV format**: Ensure no missing columns or malformed data
2. **Check file permissions**: Ensure system can read CSV file
3. **Force reload**: Run manual reload command above
4. **Contact tech team**: If issues persist

---

## 📋 **Best Practices**

### ✅ **Do's**
- Keep backups of CSV before major changes
- Use clear, customer-friendly language
- Include relevant keywords for search
- Test content with sample customer questions
- Update the `atualizado_em` field when making changes

### ❌ **Don'ts**  
- Don't change column headers in CSV
- Don't delete existing entries without coordination
- Don't use special characters that break CSV format
- Don't make changes during peak hours (if possible)

---

## 🚀 **Future Enhancements**

### Planned Improvements:
1. **Web Interface**: Simple form for adding knowledge entries
2. **Change Notifications**: Email alerts when knowledge base updates
3. **Analytics**: Track which knowledge entries are most accessed
4. **A/B Testing**: Test different content versions
5. **Auto-suggestions**: AI suggests knowledge gaps to fill

---

## 📞 **Support**

### For Questions About:
- **CSV format**: Contact tech team
- **Content strategy**: Contact product team  
- **System status**: Check startup logs or contact tech team
- **Access issues**: Contact IT for file permissions

### Emergency Contact:
- **System down**: Contact tech team immediately
- **Urgent content update**: Use force-reload command

---

*This system follows the KISS principle: Keep It Simple, Stupid. Management can focus on content while the system handles all technical complexity automatically.* 🎯