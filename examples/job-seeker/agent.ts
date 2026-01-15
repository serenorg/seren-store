/**
 * Job Seeker Agent
 *
 * Matches resumes to job opportunities and provides tailored recommendations
 * for improving job applications.
 *
 * Price: $0.06 per invocation
 */

import { agent } from "seren-agent";
import { getOpenAIClient } from "seren-agent/llm";

interface JobMatch {
  score: number; // 0-100
  job_title: string;
  match_reasons: string[];
  gaps: string[];
  suggestions: string[];
}

interface SkillAnalysis {
  skill: string;
  proficiency: "beginner" | "intermediate" | "advanced" | "expert";
  relevance: "high" | "medium" | "low";
  evidence: string;
}

interface JobSeekerResult {
  overall_score: number;
  matches: JobMatch[];
  skill_analysis: SkillAnalysis[];
  resume_summary: string;
  improvement_suggestions: string[];
  keywords_to_add: string[];
  metadata: {
    jobs_analyzed: number;
    top_match_score: number;
    skills_identified: number;
  };
}

interface JobSeekerInput {
  resume: string;
  job_descriptions?: string[];
  target_role?: string;
  industry?: string;
  experience_level?: "entry" | "mid" | "senior" | "executive";
}

export const run = agent(
  {
    name: "Job Seeker",
    description:
      "Match your resume to job opportunities and get personalized recommendations. " +
      "Provide your resume and optionally job descriptions to match against.",
    price: "0.06",
  },
  async (
    input: JobSeekerInput,
  ): Promise<JobSeekerResult | { error: string }> => {
    const {
      resume,
      job_descriptions,
      target_role,
      industry,
      experience_level,
    } = input;

    if (!resume) {
      return { error: "Missing required field: resume" };
    }

    const client = getOpenAIClient();

    // First, analyze the resume
    const resumeAnalysisPrompt = `Analyze this resume and extract:
1. Key skills with proficiency levels
2. Years of experience
3. Main achievements
4. Career trajectory
5. Industry focus

Resume:
${resume}

${target_role ? `Target role: ${target_role}` : ""}
${industry ? `Target industry: ${industry}` : ""}
${experience_level ? `Experience level: ${experience_level}` : ""}

Return as JSON:
{
    "skills": [{"skill": "...", "proficiency": "beginner|intermediate|advanced|expert", "evidence": "..."}],
    "years_experience": number,
    "achievements": ["..."],
    "career_summary": "...",
    "strengths": ["..."],
    "areas_for_improvement": ["..."]
}`;

    try {
      const resumeResponse = await client.chat.completions.create({
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content: "You are an expert resume analyst and career coach.",
          },
          { role: "user", content: resumeAnalysisPrompt },
        ],
        temperature: 0.3,
        response_format: { type: "json_object" },
      });

      const resumeAnalysis = JSON.parse(
        resumeResponse.choices[0]?.message?.content || "{}",
      );

      // If job descriptions provided, match against them
      const matches: JobMatch[] = [];

      if (job_descriptions && job_descriptions.length > 0) {
        for (const jobDesc of job_descriptions.slice(0, 5)) {
          // Limit to 5 jobs
          const matchPrompt = `Compare this resume to the job description and provide a match analysis.

Resume Summary:
${resumeAnalysis.career_summary}
Skills: ${resumeAnalysis.skills?.map((s: SkillAnalysis) => s.skill).join(", ")}

Job Description:
${jobDesc}

Return as JSON:
{
    "score": 0-100,
    "job_title": "extracted or inferred title",
    "match_reasons": ["why this is a good match"],
    "gaps": ["skills or experience the candidate lacks"],
    "suggestions": ["how to improve application for this role"]
}`;

          const matchResponse = await client.chat.completions.create({
            model: "gpt-4o-mini",
            messages: [
              {
                role: "system",
                content:
                  "You are an expert recruiter matching candidates to jobs.",
              },
              { role: "user", content: matchPrompt },
            ],
            temperature: 0.3,
            response_format: { type: "json_object" },
          });

          const matchResult = JSON.parse(
            matchResponse.choices[0]?.message?.content || "{}",
          );
          matches.push({
            score: Math.min(100, Math.max(0, matchResult.score || 0)),
            job_title: matchResult.job_title || "Unknown Position",
            match_reasons: matchResult.match_reasons || [],
            gaps: matchResult.gaps || [],
            suggestions: matchResult.suggestions || [],
          });
        }
      }

      // Generate improvement suggestions
      const improvementPrompt = `Based on this resume analysis, provide actionable improvement suggestions.

Analysis:
${JSON.stringify(resumeAnalysis, null, 2)}

${target_role ? `Target role: ${target_role}` : ""}
${industry ? `Target industry: ${industry}` : ""}

Return as JSON:
{
    "suggestions": ["specific, actionable improvement"],
    "keywords_to_add": ["ATS-friendly keywords to include"],
    "formatting_tips": ["resume formatting suggestions"]
}`;

      const improvementResponse = await client.chat.completions.create({
        model: "gpt-4o-mini",
        messages: [
          {
            role: "system",
            content: "You are an expert resume writer and career coach.",
          },
          { role: "user", content: improvementPrompt },
        ],
        temperature: 0.4,
        response_format: { type: "json_object" },
      });

      const improvements = JSON.parse(
        improvementResponse.choices[0]?.message?.content || "{}",
      );

      // Build skill analysis with relevance
      const skillAnalysis: SkillAnalysis[] = (resumeAnalysis.skills || []).map(
        (s: { skill: string; proficiency: string; evidence: string }) => ({
          skill: s.skill,
          proficiency: s.proficiency as SkillAnalysis["proficiency"],
          relevance: target_role
            ? s.skill.toLowerCase().includes(target_role.toLowerCase())
              ? "high"
              : "medium"
            : ("medium" as const),
          evidence: s.evidence,
        }),
      );

      // Calculate overall score
      const overallScore =
        matches.length > 0
          ? Math.round(
              matches.reduce((sum, m) => sum + m.score, 0) / matches.length,
            )
          : Math.round(
              (skillAnalysis.filter(
                (s) =>
                  s.proficiency === "advanced" || s.proficiency === "expert",
              ).length /
                Math.max(1, skillAnalysis.length)) *
                100,
            );

      // Sort matches by score
      matches.sort((a, b) => b.score - a.score);

      return {
        overall_score: overallScore,
        matches,
        skill_analysis: skillAnalysis,
        resume_summary:
          resumeAnalysis.career_summary || "Resume analyzed successfully.",
        improvement_suggestions: [
          ...(improvements.suggestions || []),
          ...(improvements.formatting_tips || []),
        ],
        keywords_to_add: improvements.keywords_to_add || [],
        metadata: {
          jobs_analyzed: matches.length,
          top_match_score: matches.length > 0 ? matches[0].score : 0,
          skills_identified: skillAnalysis.length,
        },
      };
    } catch (error) {
      return {
        error: `Analysis failed: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  },
);

// Local testing (run with: npx ts-node agent.ts)
const isMainModule = typeof require !== "undefined" && require.main === module;
if (isMainModule) {
  const sampleResume = `
John Smith
Senior Software Engineer
john.smith@email.com | San Francisco, CA

EXPERIENCE

Senior Software Engineer | TechCorp Inc. | 2020-Present
- Led development of microservices architecture serving 1M+ users
- Implemented CI/CD pipelines reducing deployment time by 60%
- Mentored team of 5 junior developers

Software Engineer | StartupXYZ | 2017-2020
- Built real-time data processing pipeline using Kafka and Spark
- Developed REST APIs using Node.js and Python
- Contributed to open-source projects with 500+ GitHub stars

SKILLS
Python, TypeScript, Go, Kubernetes, AWS, PostgreSQL, Redis

EDUCATION
BS Computer Science, UC Berkeley, 2017
`;

  const sampleJob = `
Senior Backend Engineer

We're looking for an experienced backend engineer to join our platform team.

Requirements:
- 5+ years of backend development experience
- Strong experience with distributed systems
- Proficiency in Python or Go
- Experience with cloud platforms (AWS/GCP)
- Kubernetes experience preferred

Nice to have:
- Experience with real-time data processing
- Open source contributions
`;

  run({
    resume: sampleResume,
    job_descriptions: [sampleJob],
    target_role: "Senior Backend Engineer",
  }).then((result) => console.log(JSON.stringify(result, null, 2)));
}
