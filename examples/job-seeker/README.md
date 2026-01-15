# Job Seeker Agent

Match your resume to job opportunities and get personalized recommendations.

## Usage

```typescript
// Input
{
    "resume": "John Smith\nSenior Software Engineer\n...",
    "job_descriptions": [           // optional: jobs to match against
        "Senior Backend Engineer\nRequirements: ..."
    ],
    "target_role": "Backend Engineer",  // optional
    "industry": "Technology",           // optional
    "experience_level": "senior"        // optional: entry, mid, senior, executive
}

// Output
{
    "overall_score": 85,
    "matches": [
        {
            "score": 92,
            "job_title": "Senior Backend Engineer",
            "match_reasons": [
                "Strong distributed systems experience",
                "5+ years relevant experience",
                "Python and Go proficiency"
            ],
            "gaps": [
                "No explicit GCP experience mentioned"
            ],
            "suggestions": [
                "Highlight Kubernetes certifications",
                "Add specific metrics for system scale"
            ]
        }
    ],
    "skill_analysis": [
        {
            "skill": "Python",
            "proficiency": "advanced",
            "relevance": "high",
            "evidence": "REST APIs, data pipeline development"
        }
    ],
    "resume_summary": "Experienced backend engineer with 6+ years...",
    "improvement_suggestions": [
        "Add quantifiable achievements to each role",
        "Include relevant certifications"
    ],
    "keywords_to_add": [
        "microservices",
        "distributed systems",
        "scalability"
    ],
    "metadata": {
        "jobs_analyzed": 1,
        "top_match_score": 92,
        "skills_identified": 7
    }
}
```

## Features

- **Resume Analysis** - Extract skills, experience, and achievements
- **Job Matching** - Score compatibility with job descriptions (0-100)
- **Gap Analysis** - Identify missing skills or experience
- **Improvement Suggestions** - Actionable recommendations
- **ATS Keywords** - Keywords to improve resume visibility

## Pricing

- **$0.06 per invocation**

## Experience Levels

| Level | Typical Experience |
|-------|-------------------|
| `entry` | 0-2 years |
| `mid` | 2-5 years |
| `senior` | 5-10 years |
| `executive` | 10+ years |

## Local Testing

```bash
cd examples/job-seeker
OPENAI_API_KEY=your-key npx ts-node agent.ts
```
