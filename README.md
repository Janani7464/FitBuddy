# FitBuddy – AI Fitness Plan Generator

A full-stack React + Express application that uses the Google Gemini API to generate a structured, general-purpose fitness plan from user preferences.

## Safety

FitBuddy is intentionally designed for adults (18+). It provides general fitness information, not medical diagnosis, treatment, or individualized medical advice.

The generated plan must avoid:
- Extreme dieting or calorie restriction
- Dangerous or high-risk exercise instructions
- Medication or supplement prescriptions
- Treatment of injuries or medical conditions
- Body-shaming or appearance-based judgments

If a user has a medical condition, injury, symptoms, or is unsure whether exercise is appropriate, the UI advises them to consult a qualified healthcare professional.

## Stack

- Frontend: React + Vite
- Backend: Node.js + Express
- AI: Google Gemini API using `@google/genai`
- Validation: Zod
- Security: Helmet
- CORS: cors
- Development: concurrently

## Project structure

```text
FitBuddy/
├── backend/
│   ├── src/
│   │   ├── config.js
│   │   ├── middleware/errorHandler.js
│   │   ├── routes/health.js
│   │   ├── routes/plan.js
│   │   ├── services/geminiService.js
│   │   ├── schemas/planSchema.js
│   │   ├── utils/prompt.js
│   │   └── server.js
│   ├── .env.example
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── .env.example
│   └── package.json
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

- Node.js 20+ recommended
- A Google Gemini API key from Google AI Studio
- VS Code

## 1. Open the project

Extract/open the `FitBuddy` folder in VS Code.

## 2. Install dependencies

From the project root:

```bash
npm install
npm run install:all
```

Or install separately:

```bash
cd backend
npm install

cd ../frontend
npm install
```

## 3. Configure Gemini

Create:

```text
backend/.env
```

Use the values from `backend/.env.example`:

```env
GEMINI_API_KEY=YOUR_REAL_KEY
GEMINI_MODEL=gemini-3.8-flash
PORT=5000
CLIENT_ORIGIN=http://localhost:5173
```

The Gemini key stays on the backend and is never sent to the browser.

## 4. Run

From the root:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

Backend health endpoint:

```text
http://localhost:5000/api/health
```

## 5. Generate a plan

1. Enter the requested profile information.
2. The app requires an age of 18 or above.
3. Choose fitness goal, experience level, days, duration, location, equipment, diet preference, and preferences.
4. Accept the safety acknowledgement.
5. Click `Generate My Plan`.
6. The React frontend calls `POST /api/plan`.
7. Express validates the request.
8. The backend sends a constrained prompt and JSON schema to Gemini.
9. Gemini returns structured JSON.
10. The backend validates the AI response.
11. The frontend renders the weekly plan.

## 6. Production build

```bash
npm run build
npm start
```

The backend does not serve the frontend automatically in this starter. For deployment, host the built `frontend/dist` with a static host or configure Express to serve it.

## 7. API

### GET /api/health

Returns:

```json
{
  "ok": true,
  "service": "fitbuddy-api"
}
```

### POST /api/plan

Example request:

```json
{
  "name": "Alex",
  "age": 25,
  "gender": "prefer-not-to-say",
  "heightCm": 170,
  "weightKg": 65,
  "goal": "general-fitness",
  "fitnessLevel": "beginner",
  "workoutDays": 3,
  "workoutDuration": 45,
  "location": "home",
  "equipment": ["bodyweight", "resistance-bands"],
  "dietaryPreference": "vegetarian",
  "preferences": "Prefer low-impact exercises.",
  "safetyAcknowledgement": true
}
```

## Testing

Run the backend:

```bash
cd backend
npm run dev
```

Health check:

```bash
curl http://localhost:5000/api/health
```

Test validation:

```bash
curl -X POST http://localhost:5000/api/plan \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Alex\",\"age\":17,\"gender\":\"prefer-not-to-say\",\"heightCm\":170,\"weightKg\":65,\"goal\":\"general-fitness\",\"fitnessLevel\":\"beginner\",\"workoutDays\":3,\"workoutDuration\":45,\"location\":\"home\",\"equipment\":[\"bodyweight\"],\"dietaryPreference\":\"vegetarian\",\"preferences\":\"\",\"safetyAcknowledgement\":true}"
```

That request should return a validation error because FitBuddy is adult-only.

## Notes about Gemini

The backend uses Google's official `@google/genai` JavaScript SDK and structured JSON output. The model name is configurable through `GEMINI_MODEL`.

If a model is unavailable for your API key/project, change `GEMINI_MODEL` to a currently available Gemini model in `backend/.env`.
