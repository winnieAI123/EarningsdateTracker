import { GoogleGenAI } from "@google/genai";
import type { Company, EarningsData, CompanyEarningsProfile } from '../types';

// Per guidelines, initialize with API key from environment variables.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

/**
 * Fetches the next earnings date for a single company using the Gemini API with Google Search grounding.
 * @param company The company to fetch earnings data for.
 * @returns A promise that resolves to an object with the earnings_date and notes.
 */
export const fetchSingleCompanyEarningsDate = async (company: Company): Promise<Pick<CompanyEarningsProfile, 'earnings_date' | 'notes'>> => {
  const model = 'gemini-2.5-flash';
  
  // Provide the current date to the model for context to find the *next* event.
  const currentDate = '2025-10-24';
  
  const prompt = `
    ATTENTION: Today's date is ${currentDate}.
    Using real-time web search, find the exact, confirmed upcoming earnings call date for the following company that is AFTER today's date.
    - Name: ${company.name}
    - Ticker: ${company.ticker}

    Your entire response MUST be a single, clean JSON object with no extra text, formatting, or markdown.
    The JSON object must have the following structure:
    {
      "company_name": "${company.name}",
      "ticker": "${company.ticker}",
      "earnings_date": "YYYY-MM-DD",
      "notes": "..."
    }

    If the date is not yet officially announced, provide the best-estimated date based on past schedules and clearly state in the "notes" that it is an estimate.
    If no reliable upcoming date can be found, set "earnings_date" to "Not announced". The notes field can explain why.
  `;
  
  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt,
      config: {
        // Enable Google Search grounding for real-time information.
        // This is incompatible with responseSchema, so we will parse the JSON manually.
        tools: [{googleSearch: {}}],
        temperature: 0.1,
      },
    });

    const responseText = response.text;
    if (!responseText) {
      throw new Error('Empty response from API');
    }

    let parsedJson: EarningsData;
    try {
      // The model is instructed to return clean JSON, but as a safeguard,
      // we'll clean up potential markdown formatting like ```json ... ```
      const cleanedJsonString = responseText.replace(/```json\n?|```/g, '').trim();
      parsedJson = JSON.parse(cleanedJsonString);
    } catch (e) {
      console.error("Failed to parse JSON response:", responseText);
      throw new Error("Invalid JSON response from API.");
    }
    
    if (parsedJson.earnings_date === "Not announced" || parsedJson.earnings_date === "Not found") {
      return {
        earnings_date: '未公布',
        notes: parsedJson.notes || '无法获取确切或预估的业绩发布日期。'
      };
    }

    return {
      earnings_date: parsedJson.earnings_date,
      notes: parsedJson.notes,
    };
  } catch (error) {
    console.error(`Error fetching earnings date for ${company.name} (${company.ticker}):`, error);
    if (error instanceof Error) {
        throw new Error(`Could not fetch data for ${company.name}: ${error.message}`);
    }
    throw new Error(`An unknown error occurred while fetching data for ${company.name}.`);
  }
};
