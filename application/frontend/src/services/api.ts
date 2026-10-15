export interface TrajectoryRecord {
  original_question?: string;
  attempt: number;
  query: string;
  score: number;
  best_score: number;
  score_delta: number;
  chunk_overlap: number;
  decision: string;
  halting_decision?: string;
  stop_probability?: number | null;
  runtime_action?: string;
  rewritten_query?: string;
}

export interface AskResponse {
  question: string;
  answer: string;
  source: string;
  trajectory: TrajectoryRecord[];
  outcome?: string;
  evidence_status?: string;
  acronym_entries?: { full_form: string; aliases: string[]; source: string }[];
}

export interface User {
  id: number;
  full_name: string;
  email: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

const API_PREFIX = import.meta.env.DEV ? "/api" : "";


export async function askHR(
  question: string
): Promise<AskResponse> {

  const token = localStorage.getItem(
    "access_token"
  );

  const response = await fetch(
    `${API_PREFIX}/ask`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",

        ...(token
          ? {
              Authorization:
                `Bearer ${token}`,
            }
          : {}),
      },

      body: JSON.stringify({
        question,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      response.status === 401 ? "Your session has expired. Please sign in again." : response.status === 429 ? "Too many requests. Please wait a minute and try again." : response.status === 503 ? "The HR service is temporarily unavailable. Please try again." : "The request could not be completed. Please check your question and try again."
    );
  }

  return response.json();
}


export async function registerUser(
  full_name: string,
  email: string,
  password: string
): Promise<User> {

  const response = await fetch(
    `${API_PREFIX}/auth/register`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        full_name,
        email,
        password,
      }),
    }
  );

  const data =
    await response.json();

  if (!response.ok) {

    throw new Error(
      data.detail ||
      "Registration failed."
    );
  }

  return data;
}


export async function loginUser(
  email: string,
  password: string
): Promise<LoginResponse> {

  const response = await fetch(
    `${API_PREFIX}/auth/login`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        email,
        password,
      }),
    }
  );

  const data =
    await response.json();

  if (!response.ok) {

    throw new Error(
      data.detail ||
      "Login failed."
    );
  }

  return data;
}


export async function getCurrentUser(): Promise<User> {

  const token =
    localStorage.getItem(
      "access_token"
    );

  if (!token) {
    throw new Error(
      "No authentication token."
    );
  }

  const response = await fetch(
    `${API_PREFIX}/auth/me`,
    {
      method: "GET",

      headers: {
        Authorization:
          `Bearer ${token}`,
      },
    }
  );

  const data =
    await response.json();

  if (!response.ok) {

    throw new Error(
      data.detail ||
      "Authentication failed."
    );
  }

  return data;
}