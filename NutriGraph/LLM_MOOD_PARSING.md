# ✨ LLM-Based Mood Parsing Feature

## Overview

Users can now describe their mood/feelings in **natural language** instead of clicking fixed buttons. The LLM intelligently parses the text, extracts symptoms, determines sentiment, and adds everything to the knowledge graph.

---

## How It Works

### User Flow

1. **User types freely:** "feeling super energized today!" or "slight headache and tired"
2. **LLM analyzes:** Extracts symptoms, sentiment, severity
3. **Graph updated:** Each symptom becomes a node, linked to recent meals
4. **Feedback shown:** User sees what was identified

---

## Backend Implementation

### New Endpoint: `/log/mood`

**File:** `backend/main.py`

```python
@app.post("/log/mood")
async def add_mood_log(mood_request: MoodTextRequest):
    """
    Accepts: {"mood_text": "feeling great and energized"}
    
    Returns: {
        "symptoms": ["High Energy", "Good Mood"],
        "sentiment": "positive",
        "severity": "high",
        "description": "Feeling great and energized",
        "message": "Logged 2 symptom(s) from your mood!"
    }
    """
```

### LLM Parsing Function

**Function:** `parse_mood_text(mood_text: str)`

**Prompt Strategy:**
- Provides structured JSON schema
- Includes examples for few-shot learning
- Asks for specific medical/health terms
- Handles sentiment analysis
- Assesses severity

**Example Transformations:**

| User Input | LLM Output |
|---|---|
| "feeling great and energized!" | symptoms: ["High Energy", "Good Mood"]<br>sentiment: positive<br>severity: high |
| "slight headache" | symptoms: ["Headache"]<br>sentiment: negative<br>severity: low |
| "tired but ok" | symptoms: ["Fatigue"]<br>sentiment: neutral<br>severity: medium |
| "super focused today" | symptoms: ["Mental Clarity", "High Focus"]<br>sentiment: positive<br>severity: high |

### Fallback Handling

If LLM fails or returns invalid JSON:
```python
return {
    "symptoms": [mood_text.strip().title()],
    "sentiment": "neutral",
    "severity": "medium",
    "description": mood_text.strip()
}
```

---

## Frontend Implementation

### New UI Component

**File:** `frontend/app.py` (lines 297-362)

**Features:**
1. **Text Input:** Large text field for free-form input
2. **AI Analysis:** Spinner while LLM processes
3. **Results Display:** Expandable section showing what was identified
4. **Quick Buttons:** Optional shortcuts for common moods

**UI Elements:**
```
💭 How Are You Feeling?
┌──────────────────────────────────────────┐
│ feeling super energized today!           │
└──────────────────────────────────────────┘
          [✨ Log Mood with AI]

Quick options:
[⚡ High Energy] [😴 Tired] [🤕 Not Great]
```

### Chat History Display

**Enhanced to show:**
- Emoji based on sentiment (😊 positive, 😔 negative, 😐 neutral)
- Symptom name
- Severity level (low/medium/high)

**Example:**
```
[10:23] 😊 High Energy (high)
[10:25] 😔 Headache (low)
```

---

## Graph Structure

### Nodes Created

For each symptom identified:

```python
# UserLog Node
{
    "node_type": "UserLog",
    "sentiment": "positive",
    "timestamp": "2025-10-04T10:23:00"
}

# Symptom Node (reused if already exists)
{
    "node_type": "Symptom",
    "name": "High Energy"
}
```

### Edges Created

```
UserLog --[EXPERIENCED]--> Symptom
Meal --[LOGGED_NEAR]--> UserLog  (if within time window)
```

### Example Graph

```
User logs: "feeling amazing after breakfast!"

Before:
Meal_1 (eggs, avocado) --[CONTAINS]--> Ingredient (eggs)

After:
Meal_1 --[LOGGED_NEAR]--> UserLog_1
UserLog_1 --[EXPERIENCED]--> Symptom (High Energy)
UserLog_1 --[EXPERIENCED]--> Symptom (Good Mood)
```

---

## API Examples

### Request

```bash
curl -X POST http://localhost:8000/log/mood \
  -H "Content-Type: application/json" \
  -d '{"mood_text": "feeling super energized and focused today!"}'
```

### Response

```json
{
  "log_ids": ["userlog_3", "userlog_4"],
  "symptoms": ["High Energy", "Mental Focus"],
  "sentiment": "positive",
  "severity": "high",
  "description": "Feeling super energized and focused",
  "timestamp": "2025-10-04T10:23:00",
  "message": "Logged 2 symptom(s) from your mood!"
}
```

---

## LLM Prompt Engineering

### Prompt Template

```
Analyze this mood/feeling description from a user and extract structured information.

User's description: "{mood_text}"

Your task:
1. Identify specific symptoms, feelings, or moods mentioned
2. Determine the overall sentiment (positive, negative, or neutral)
3. Assess the severity/intensity (low, medium, or high)
4. Create a clean, normalized description

Return ONLY a valid JSON object with this exact structure:
{
    "symptoms": ["feeling1", "feeling2", ...],
    "sentiment": "positive|negative|neutral",
    "severity": "low|medium|high",
    "description": "clean description"
}

Examples:
- Input: "feeling great and energized!" 
  → {"symptoms": ["High Energy", "Good Mood"], "sentiment": "positive", "severity": "high", ...}
```

### Why This Works

1. **Structured Output:** JSON schema forces consistent format
2. **Few-Shot Learning:** Examples guide the model
3. **Clear Instructions:** Specific tasks enumerated
4. **Constraints:** "positive|negative|neutral" limits options
5. **Medical Terms:** Asks for specific health vocabulary

---

## Testing

### Test Cases

```python
# Test 1: Simple positive mood
Input: "feeling great!"
Expected: symptoms=["Good Mood"], sentiment="positive"

# Test 2: Multiple symptoms
Input: "headache and tired"
Expected: symptoms=["Headache", "Fatigue"], sentiment="negative"

# Test 3: Mixed sentiment
Input: "tired but happy"
Expected: symptoms=["Fatigue", "Good Mood"], sentiment="neutral"

# Test 4: Severity detection
Input: "extreme headache"
Expected: symptoms=["Headache"], severity="high"

# Test 5: Vague input
Input: "meh"
Expected: symptoms=["Low Mood"], sentiment="neutral", severity="low"
```

### Manual Testing Steps

1. **Start services:**
   ```bash
   python backend\main.py
   streamlit run frontend\app.py
   ```

2. **Test the UI:**
   - Type: "feeling super energized today!"
   - Click "✨ Log Mood with AI"
   - Check expander shows: symptoms, sentiment, severity
   - Verify chat history shows the mood with emoji

3. **Check backend logs:**
   ```
   [API] Parsing mood text: 'feeling super energized today!'
   [API] Parsed symptoms: ['High Energy', 'Good Mood']
   [API] Sentiment: positive, Severity: high
   [API] Added symptom 'High Energy' to graph: userlog_1
   [API] Added symptom 'Good Mood' to graph: userlog_2
   ```

4. **Check graph:**
   - View graph visualization
   - See new Symptom nodes
   - See UserLog nodes connected to symptoms
   - See LOGGED_NEAR edges to recent meals

---

## Benefits

### vs. Fixed Buttons

| Fixed Buttons | LLM Parsing |
|---|---|
| Limited options | Unlimited expressions |
| Pre-defined symptoms | Custom symptoms |
| No severity info | Auto-detects severity |
| Single symptom | Multiple symptoms |
| "Click High Energy" | "feeling great and energized!" |

### User Experience

1. **Natural:** Users express themselves freely
2. **Detailed:** Captures nuances (severity, multiple symptoms)
3. **Smart:** LLM normalizes to medical terms
4. **Transparent:** Shows what was identified

### Graph Quality

1. **Richer Data:** More symptom variety
2. **Better Correlations:** Severity adds dimension
3. **True User Voice:** Not constrained by UI
4. **Multi-symptom:** Captures complex states

---

## Future Enhancements

### 1. Symptom Suggestions
```
User types: "head"
Autocomplete: "Headache", "Head Pressure", "Migraine"
```

### 2. Temporal Analysis
```
LLM extracts time: "felt great this morning"
→ Backdate symptom to morning timestamp
```

### 3. Intensity Scaling
```
Current: low/medium/high
Future: 1-10 numerical scale
```

### 4. Cause Attribution
```
Input: "headache from coffee"
LLM: symptom="Headache", potential_cause="coffee"
→ Create special edge to coffee ingredient
```

### 5. Multi-language
```
LLM can parse: "me siento muy bien" → High Energy
```

---

## Troubleshooting

### Issue: LLM returns invalid JSON

**Symptoms:** Error in backend logs
**Cause:** Markdown wrapping or malformed JSON
**Fix:** Already handled with fallback

**Code:**
```python
if response_text.startswith("```"):
    # Strip markdown code blocks
    response_text = response_text.replace("```json", "").replace("```", "")
```

### Issue: Empty symptoms list

**Symptoms:** No symptoms identified
**Cause:** Very vague input like "ok" or "fine"
**Fix:** Fallback treats input as symptom name

### Issue: Wrong sentiment

**Symptoms:** "tired but happy" → negative
**Cause:** LLM focuses on "tired"
**Fix:** More examples in prompt, or user feedback loop

---

## Code Changes Summary

### Backend (`backend/main.py`)

**Added:**
- `MoodTextRequest` model (line 64)
- `parse_mood_text()` function (line 93)
- `/log/mood` endpoint (line 375)

**Modified:**
- None (existing `/log` endpoint still works)

### Frontend (`frontend/app.py`)

**Added:**
- `log_mood_text()` function (line 145)
- Mood input UI (lines 297-362)
- `mood_log` chat display (lines 384-389)

**Modified:**
- Chat history rendering to include mood_log type

---

## Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can type mood in text box
- [ ] Click "Log Mood with AI" works
- [ ] Expander shows parsed info
- [ ] Chat history shows mood with emoji
- [ ] Backend logs show parsing details
- [ ] Graph visualization shows new symptom nodes
- [ ] Quick buttons work
- [ ] Multiple symptoms detected from one input
- [ ] Sentiment is correct (positive/negative/neutral)
- [ ] Severity is reasonable (low/medium/high)

---

## Performance

**LLM Call:** ~1-2 seconds per mood log
**Acceptable:** Yes, happens in background with spinner
**Optimization:** Could batch multiple moods, but not needed for MVP

---

## Summary

✅ **Users can now express moods naturally**
✅ **LLM extracts structured symptoms**
✅ **All symptoms added to graph**
✅ **UI shows what was identified**
✅ **Maintains all existing functionality**
✅ **Fallback handles errors gracefully**

**Status:** Ready to test! 🚀
