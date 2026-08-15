import {
  createContext,
  useContext,
  useEffect,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import {
  BarChart3,
  Clock3,
  FileText,
  Home,
  LogIn,
  LogOut,
  MessageSquare,
  Settings,
  User,
  UserPlus,
} from "lucide-react";

import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router";

import {
  askHR,
  getCurrentUser,
  loginUser,
  registerUser,
  type AskResponse,
  type TrajectoryRecord,
  type User as AppUser,
} from "./services/api";



type NavItem = {
  label: string;
  path: string;
  icon: typeof Home;
};

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    path: "/",
    icon: Home,
  },
  {
    label: "Ask HR",
    path: "/chat",
    icon: MessageSquare,
  },
  {
    label: "History",
    path: "/history",
    icon: Clock3,
  },
  {
    label: "Analytics",
    path: "/analytics",
    icon: BarChart3,
  },
  {
    label: "Policies",
    path: "/policies",
    icon: FileText,
  },
  {
    label: "Settings",
    path: "/settings",
    icon: Settings,
  },
];


/* =========================================================
   AUTH CONTEXT
========================================================= */



type AuthContextType = {
  user: AppUser | null;
  loading: boolean;
  login: (
    email: string,
    password: string
  ) => Promise<void>;
  signup: (
    fullName: string,
    email: string,
    password: string
  ) => Promise<void>;
  logout: () => void;
};

const AuthContext =
  createContext<AuthContextType | undefined>(
    undefined
  );


function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [user, setUser] =
    useState<AppUser | null>(null);

  const [loading, setLoading] =
    useState(true);


  useEffect(() => {

    const token =
      localStorage.getItem(
        "access_token"
      );

    if (!token) {
      setLoading(false);
      return;
    }


    getCurrentUser()
      .then((currentUser) => {
        setUser(currentUser);
      })
      .catch(() => {
        localStorage.removeItem(
          "access_token"
        );
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });

  }, []);


  async function login(
    email: string,
    password: string
  ) {

    const result =
      await loginUser(
        email,
        password
      );

    localStorage.setItem(
      "access_token",
      result.access_token
    );

    setUser(result.user);
  }


  async function signup(
    fullName: string,
    email: string,
    password: string
  ) {

    await registerUser(
      fullName,
      email,
      password
    );
  }


  function logout() {

    localStorage.removeItem(
      "access_token"
    );

    setUser(null);
  }


  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}


function useAuth() {

  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}


/* =========================================================
   PROTECTED ROUTE
========================================================= */

function ProtectedRoute({
  children,
}: {
  children: ReactNode;
}) {

  const {
    user,
    loading,
  } = useAuth();


  if (loading) {

    return (
      <LoadingScreen />
    );
  }


  if (!user) {

    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  return children;
}


/* =========================================================
   APP ROUTER
========================================================= */

export default function App() {

  return (
    <BrowserRouter>

      <AuthProvider>

        <Routes>

          {/* Public */}

          <Route
            path="/login"
            element={<LoginPage />}
          />

          <Route
            path="/signup"
            element={<SignupPage />}
          />


          {/* Protected */}

          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          />

        </Routes>

      </AuthProvider>

    </BrowserRouter>
  );
}


/* =========================================================
   LOGIN
========================================================= */

function LoginPage() {

  const navigate =
    useNavigate();

  const {
    user,
    login,
  } = useAuth();


  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [loading, setLoading] =
    useState(false);


  useEffect(() => {

    if (user) {
      navigate("/", {
        replace: true,
      });
    }

  }, [
    user,
    navigate,
  ]);


  async function handleSubmit(
    event: FormEvent
  ) {

    event.preventDefault();

    setError("");

    if (!email.trim()) {
      setError(
        "Please enter your email."
      );
      return;
    }

    if (!password) {
      setError(
        "Please enter your password."
      );
      return;
    }


    setLoading(true);


    try {

      await login(
        email.trim(),
        password
      );

      navigate("/", {
        replace: true,
      });

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Login failed."
      );

    } finally {

      setLoading(false);

    }

  }


  return (
    <AuthShell>

      <div className="mb-8 text-center">

        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-lg">
          <LogIn size={26} />
        </div>

        <h1 className="mt-5 text-3xl font-bold text-slate-950">
          Welcome back
        </h1>

        <p className="mt-2 text-slate-500">
          Sign in to your HR RAG workspace.
        </p>

      </div>


      <form
        onSubmit={handleSubmit}
        className="space-y-4"
      >

        <Field
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="you@example.com"
        />


        <Field
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="Your password"
        />


        {error && (
          <ErrorBox
            message={error}
          />
        )}


        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading
            ? "Signing in..."
            : "Sign In"}
        </button>

      </form>


      <p className="mt-6 text-center text-sm text-slate-500">

        Don't have an account?{" "}

        <Link
          to="/signup"
          className="font-semibold text-emerald-700 hover:text-emerald-800"
        >
          Create one
        </Link>

      </p>

    </AuthShell>
  );
}


/* =========================================================
   SIGNUP
========================================================= */

function SignupPage() {

  const navigate =
    useNavigate();

  const {
    user,
    signup,
  } = useAuth();


  const [fullName, setFullName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  const [loading, setLoading] =
    useState(false);


  useEffect(() => {

    if (user) {
      navigate("/", {
        replace: true,
      });
    }

  }, [
    user,
    navigate,
  ]);


  async function handleSubmit(
    event: React.FormEvent
  ) {

    event.preventDefault();

    setError("");
    setSuccess("");


    if (fullName.trim().length < 2) {

      setError(
        "Please enter your full name."
      );

      return;
    }


    if (!email.trim()) {

      setError(
        "Please enter your email."
      );

      return;
    }


    if (password.length < 8) {

      setError(
        "Password must contain at least 8 characters."
      );

      return;
    }


    if (
      password !==
      confirmPassword
    ) {

      setError(
        "Passwords do not match."
      );

      return;
    }


    setLoading(true);


    try {

      await signup(
        fullName.trim(),
        email.trim(),
        password
      );


      setSuccess(
        "Account created successfully. Redirecting to login..."
      );


      setTimeout(() => {

        navigate("/login");

      }, 900);


    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Signup failed."
      );

    } finally {

      setLoading(false);

    }

  }


  return (
    <AuthShell>

      <div className="mb-8 text-center">

        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-lg">
          <UserPlus size={26} />
        </div>

        <h1 className="mt-5 text-3xl font-bold text-slate-950">
          Create your account
        </h1>

        <p className="mt-2 text-slate-500">
          Create a secure workspace for HR policy questions.
        </p>

      </div>


      <form
        onSubmit={handleSubmit}
        className="space-y-4"
      >

        <Field
          label="Full name"
          type="text"
          value={fullName}
          onChange={setFullName}
          placeholder="Demo User"
        />


        <Field
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="you@example.com"
        />


        <Field
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="At least 8 characters"
        />


        <Field
          label="Confirm password"
          type="password"
          value={confirmPassword}
          onChange={setConfirmPassword}
          placeholder="Repeat your password"
        />


        {error && (
          <ErrorBox
            message={error}
          />
        )}


        {success && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
            {success}
          </div>
        )}


        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-emerald-700 px-4 py-3 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading
            ? "Creating account..."
            : "Create Account"}
        </button>

      </form>


      <p className="mt-6 text-center text-sm text-slate-500">

        Already have an account?{" "}

        <Link
          to="/login"
          className="font-semibold text-emerald-700 hover:text-emerald-800"
        >
          Sign in
        </Link>

      </p>

    </AuthShell>
  );
}


/* =========================================================
   AUTH SHELL
========================================================= */

function AuthShell({
  children,
}: {
  children: ReactNode;
}) {

  return (
    <div className="min-h-screen bg-slate-100 px-4 py-10">

      <div className="mx-auto w-full max-w-md">

        <div className="mb-8 text-center">

          <div className="flex items-center justify-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-600 text-white">
              <MessageSquare size={22} />
            </div>

            <span className="text-xl font-bold text-slate-950">
              HR RAG
            </span>

          </div>

          <p className="mt-2 text-sm text-slate-500">
            Self-Correcting HR Policy Assistant
          </p>

        </div>


        <div className="rounded-2xl bg-white p-6 shadow-xl sm:p-8">

          {children}

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   MAIN LAYOUT
========================================================= */

function Layout() {

  const location =
    useLocation();

  const {
    user,
    logout,
  } = useAuth();


  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">

      <div className="flex min-h-screen">

        <aside className="hidden w-64 shrink-0 border-r border-slate-800 bg-slate-950 p-5 text-white md:block">

          <div className="mb-8">

            <div className="flex items-center gap-3">

              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600">
                <MessageSquare size={21} />
              </div>

              <div>

                <h1 className="text-xl font-bold">
                  HR RAG
                </h1>

                <p className="text-xs text-slate-400">
                  Self-Correcting Assistant
                </p>

              </div>

            </div>

          </div>


          <nav className="space-y-2">

            {navItems.map(
              (item) => {

                const Icon =
                  item.icon;

                const active =
                  location.pathname ===
                  item.path;


                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={
                      active
                        ? "flex items-center gap-3 rounded-xl bg-emerald-600 px-3 py-2.5 text-sm font-medium text-white"
                        : "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-300 transition hover:bg-slate-800 hover:text-white"
                    }
                  >
                    <Icon size={18} />

                    {item.label}
                  </Link>
                );

              }
            )}

          </nav>


          <div className="mt-8 border-t border-slate-800 pt-6">

            <button
              type="button"
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 transition hover:bg-slate-800 hover:text-white"
            >
              <LogOut size={18} />

              Logout
            </button>

          </div>

        </aside>


        <main className="min-w-0 flex-1">

          <header className="border-b bg-white px-5 py-4 md:px-6">

            <div className="flex items-center justify-between">

              <div>

                <p className="text-sm text-slate-500">
                  HR Policy Assistant
                </p>

                <h2 className="text-lg font-semibold">
                  Self-Correcting RAG
                </h2>

              </div>


              <div className="flex items-center gap-3">

                <Link
                  to="/settings"
                  className="rounded-full bg-slate-100 p-2 text-slate-700 transition hover:bg-slate-200"
                >
                  <Settings size={18} />
                </Link>


                <div className="hidden text-right sm:block">

                  <p className="text-sm font-medium">
                    {user?.full_name}
                  </p>

                  <p className="text-xs text-slate-500">
                    {user?.email}
                  </p>

                </div>


                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-800">
                  <User size={18} />
                </div>

              </div>

            </div>

          </header>


          <div className="border-b bg-white px-4 py-3 md:hidden">

            <div className="flex gap-2 overflow-x-auto">

              {navItems.map(
                (item) => {

                  const Icon =
                    item.icon;

                  const active =
                    location.pathname ===
                    item.path;


                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={
                        active
                          ? "flex shrink-0 items-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-medium text-white"
                          : "flex shrink-0 items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 text-xs font-medium text-slate-600"
                      }
                    >
                      <Icon size={15} />

                      {item.label}
                    </Link>
                  );

                }
              )}

            </div>

          </div>


          <div className="p-4 md:p-6">

            <Routes>

              <Route
                path="/"
                element={<Dashboard />}
              />

              <Route
                path="/chat"
                element={<Chat />}
              />

              <Route
                path="/history"
                element={<History />}
              />

              <Route
                path="/analytics"
                element={<Analytics />}
              />

              <Route
                path="/policies"
                element={<Policies />}
              />

              <Route
                path="/settings"
                element={<SettingsPage />}
              />

              <Route
                path="*"
                element={
                  <Navigate
                    to="/"
                    replace
                  />
                }
              />

            </Routes>

          </div>

        </main>

      </div>

    </div>
  );
}


/* =========================================================
   DASHBOARD
========================================================= */

function Dashboard() {

  return (
    <div className="mx-auto max-w-7xl space-y-6">

      <div>

        <h1 className="text-3xl font-bold text-slate-950">
          Welcome back 👋
        </h1>

        <p className="mt-1 text-slate-500">
          Monitor the HR RAG system and inspect
          the learned halting policy.
        </p>

      </div>


      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <StatCard
          title="Questions Tested"
          value="23"
          description="Evaluation questions"
        />

        <StatCard
          title="Retrieval Success"
          value="82.6%"
          description="19 of 23 questions"
        />

        <StatCard
          title="Average Attempts"
          value="1.217"
          description="Fixed and learned"
        />

        <StatCard
          title="Proxy Reduction"
          value="8.11%"
          description="Estimated workload"
        />

      </div>


      <div className="grid gap-6 xl:grid-cols-3">

        <div className="rounded-2xl bg-white p-6 shadow-sm xl:col-span-2">

          <div className="flex items-center justify-between">

            <div>

              <h2 className="text-lg font-semibold">
                Recent Questions
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Example evaluation runs.
              </p>

            </div>

            <Link
              to="/history"
              className="text-sm font-medium text-emerald-700"
            >
              View history
            </Link>

          </div>


          <div className="mt-5 space-y-3">

            <QuestionItem
              question="leave after joining"
              score="0.78"
              attempts="2"
              status="STOP"
            />

            <QuestionItem
              question="Can sick leave be carried forward?"
              score="0.90"
              attempts="1"
              status="STOP"
            />

            <QuestionItem
              question="What are the hybrid work eligibility requirements?"
              score="0.89"
              attempts="1"
              status="STOP"
            />

          </div>

        </div>


        <div className="rounded-2xl bg-slate-950 p-6 text-white">

          <div className="flex items-center gap-2">

            <BarChart3 size={20} />

            <h2 className="font-semibold">
              Policy Snapshot
            </h2>

          </div>


          <p className="mt-6 text-4xl font-bold">
            8.11%
          </p>

          <p className="mt-1 text-sm text-slate-400">
            proxy-call workload reduction
          </p>


          <div className="mt-6 space-y-3">

            <Snapshot
              label="Learned CONTINUE"
              value="6"
            />

            <Snapshot
              label="Useful CONTINUE"
              value="83.3%"
            />

          </div>

        </div>

      </div>


      <div className="rounded-2xl bg-white p-6 shadow-sm">

        <h2 className="text-lg font-semibold">
          System Flow
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Current project architecture.
        </p>


        <div className="mt-6 grid gap-3 md:grid-cols-5">

          <FlowStep
            number="1"
            title="Retrieve"
            text="ChromaDB"
          />

          <FlowStep
            number="2"
            title="Critic"
            text="Evaluate context"
          />

          <FlowStep
            number="3"
            title="Halting"
            text="STOP / CONTINUE"
          />

          <FlowStep
            number="4"
            title="Rewrite"
            text="Improve query"
          />

          <FlowStep
            number="5"
            title="Answer"
            text="Gemini / fallback"
          />

        </div>

      </div>

    </div>
  );
}


/* =========================================================
   CHAT
========================================================= */

function Chat() {

  const [question, setQuestion] =
    useState("");

  const [result, setResult] =
    useState<AskResponse | null>(
      null
    );

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  async function handleAsk() {

    const trimmed =
      question.trim();


    if (!trimmed) {

      setError(
        "Please enter a question."
      );

      return;
    }


    setLoading(true);
    setError("");
    setResult(null);


    try {

      const data =
        await askHR(trimmed);

      setResult(data);

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      );

    } finally {

      setLoading(false);

    }

  }


  function handleKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>
  ) {

    if (
      event.key === "Enter" &&
      (event.ctrlKey ||
        event.metaKey)
    ) {

      event.preventDefault();

      void handleAsk();

    }

  }


  return (
    <div className="mx-auto max-w-6xl space-y-6">

      <div>

        <h1 className="text-3xl font-bold">
          Ask HR
        </h1>

        <p className="mt-1 text-slate-500">
          Ask a policy question and inspect
          the self-correcting retrieval process.
        </p>

      </div>


      <div className="rounded-2xl bg-white p-6 shadow-sm">

        <label
          htmlFor="question"
          className="mb-3 block text-sm font-medium text-slate-700"
        >
          Your question
        </label>


        <textarea
          id="question"
          value={question}
          onChange={(event) =>
            setQuestion(
              event.target.value
            )
          }
          onKeyDown={handleKeyDown}
          disabled={loading}
          className="min-h-36 w-full rounded-xl border border-slate-300 p-4 outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
          placeholder="Example: Can an employee on probation take leave?"
        />


        <div className="mt-4 flex flex-wrap items-center gap-3">

          <button
            type="button"
            onClick={() =>
              void handleAsk()
            }
            disabled={loading}
            className="rounded-xl bg-emerald-700 px-5 py-3 font-medium text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading
              ? "Running RAG..."
              : "Ask Question"}
          </button>


          <span className="text-xs text-slate-500">
            Ctrl + Enter to submit
          </span>

        </div>


        {error && (
          <ErrorBox
            message={error}
          />
        )}

      </div>


      {loading && (
        <div className="rounded-2xl bg-white p-6 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-emerald-600" />

            <div>

              <p className="font-medium">
                Running self-correcting RAG...
              </p>

              <p className="text-sm text-slate-500">
                Retrieving, evaluating, and deciding
                whether another attempt is needed.
              </p>

            </div>

          </div>

        </div>
      )}


      {result && (
        <>

          <div className="rounded-2xl bg-white p-6 shadow-sm">

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

              <div>

                <p className="text-sm text-slate-500">
                  Final Answer
                </p>

                <h2 className="mt-1 text-xl font-semibold">
                  HR Policy Response
                </h2>

              </div>


              <span className="w-fit rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                Policy retrieved
              </span>

            </div>


            <div className="mt-5 whitespace-pre-wrap leading-7 text-slate-700">
              {result.answer}
            </div>


            <div className="mt-5 border-t pt-4 text-sm text-slate-500">
              <span className="font-medium">
                Source:
              </span>{" "}
              {result.source}
            </div>

          </div>


          <TrajectoryPanel
            trajectory={
              result.trajectory
            }
          />

        </>
      )}

    </div>
  );
}


/* =========================================================
   TRAJECTORY
========================================================= */

function TrajectoryPanel({
  trajectory,
}: {
  trajectory: TrajectoryRecord[];
}) {

  const last =
    trajectory.length
      ? trajectory[
          trajectory.length - 1
        ]
      : null;


  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm">

      <div className="flex flex-col gap-4">

        <div>

          <h2 className="text-xl font-semibold">
            Learned Retrieval Trajectory
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Inspect the critic and learned halting
            decisions at every attempt.
          </p>

        </div>


        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">

          <SummaryBox
            label="Attempts"
            value={String(
              trajectory.length
            )}
          />

          <SummaryBox
            label="Final Score"
            value={
              last
                ? last.score.toFixed(2)
                : "-"
            }
          />

          <SummaryBox
            label="Critic"
            value={
              last?.decision ||
              "-"
            }
          />

          <SummaryBox
            label="Halting"
            value={
              last?.halting_decision ||
              (
                last?.decision ===
                "SUFFICIENT"
                  ? "STOP"
                  : "-"
              )
            }
          />

        </div>

      </div>


      <div className="mt-6 space-y-4">

        {trajectory.map(
          (record, index) => (

            <TrajectoryCard
              key={`${record.attempt}-${index}`}
              record={record}
            />

          )
        )}

      </div>

    </div>
  );
}


function TrajectoryCard({
  record,
}: {
  record: TrajectoryRecord;
}) {

  const critic =
    String(
      record.decision || ""
    ).toUpperCase();


  const halting =
    String(
      record.halting_decision || ""
    ).toUpperCase();


  const action =
    String(
      record.runtime_action || ""
    ).toUpperCase();


  const isStop =
    halting === "STOP" ||
    critic === "SUFFICIENT";


  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">

      <div className="flex items-center justify-between">

        <h3 className="font-semibold">
          Attempt {record.attempt}
        </h3>


        <span
          className={
            isStop
              ? "rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800"
              : "rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800"
          }
        >
          {halting ||
            (
              critic === "SUFFICIENT"
                ? "STOP"
                : "CONTINUE"
            )}
        </span>

      </div>


      <div className="mt-4">

        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Query
        </p>

        <div className="mt-1 rounded-xl border bg-white p-3 text-sm">
          {record.query}
        </div>

      </div>


      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

        <Metric
          label="Critic Score"
          value={record.score.toFixed(2)}
        />

        <Metric
          label="Best Score"
          value={record.best_score.toFixed(2)}
        />

        <Metric
          label="Score Delta"
          value={record.score_delta.toFixed(2)}
        />

        <Metric
          label="Chunk Overlap"
          value={record.chunk_overlap.toFixed(2)}
        />

      </div>


      <div className="mt-4 grid gap-3 sm:grid-cols-2">

        <DecisionBox
          label="Critic Decision"
          value={critic}
        />

        <DecisionBox
          label="Halting Decision"
          value={
            record.halting_decision ||
            (
              critic === "SUFFICIENT"
                ? "STOP"
                : "-"
            )
          }
        />

        <DecisionBox
          label="STOP Probability"
          value={
            record.stop_probability == null
              ? "-"
              : record.stop_probability.toFixed(
                  2
                )
          }
        />

        <DecisionBox
          label="Runtime Action"
          value={action || "-"}
        />

      </div>


      {record.rewritten_query && (
        <div className="mt-4">

          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Rewritten Query
          </p>

          <div className="mt-1 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            {record.rewritten_query}
          </div>

        </div>
      )}

    </div>
  );
}


/* =========================================================
   OTHER PAGES
========================================================= */

function History() {

  return (
    <PlaceholderPage
      icon={
        <Clock3 size={28} />
      }
      title="Question History"
      description="Previous questions and trajectories will be connected to the user account next."
    />
  );
}


function Analytics() {

  return (
    <div className="mx-auto max-w-6xl space-y-6">

      <div>

        <h1 className="text-3xl font-bold">
          Analytics
        </h1>

        <p className="mt-1 text-slate-500">
          Current evaluation results.
        </p>

      </div>


      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <StatCard
          title="CV Accuracy"
          value="70.4%"
          description="Question-level 5-fold"
        />

        <StatCard
          title="Macro F1"
          value="0.61"
          description="Group-aware evaluation"
        />

        <StatCard
          title="Retrieval Success"
          value="82.6%"
          description="19 / 23 questions"
        />

        <StatCard
          title="Proxy Reduction"
          value="8.11%"
          description="37 → 34 calls"
        />

      </div>

    </div>
  );
}


function Policies() {

  return (
    <PlaceholderPage
      icon={
        <FileText size={28} />
      }
      title="Policy Documents"
      description="Policy document management will be connected next."
    />
  );
}


function SettingsPage() {

  return (
    <PlaceholderPage
      icon={
        <Settings size={28} />
      }
      title="Settings"
      description="Profile and application settings will be connected next."
    />
  );
}


/* =========================================================
   REUSABLE COMPONENTS
========================================================= */

function Field({
  label,
  type,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  type: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {

  return (
    <div>

      <label className="mb-2 block text-sm font-medium text-slate-700">
        {label}
      </label>

      <input
        type={type}
        value={value}
        onChange={(event) =>
          onChange(
            event.target.value
          )
        }
        placeholder={placeholder}
        className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100"
      />

    </div>
  );
}


function ErrorBox({
  message,
}: {
  message: string;
}) {

  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      {message}
    </div>
  );
}


function LoadingScreen() {

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100">

      <div className="text-center">

        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-emerald-600" />

        <p className="mt-4 text-sm text-slate-500">
          Checking your session...
        </p>

      </div>

    </div>
  );
}


function StatCard({
  title,
  value,
  description,
}: {
  title: string;
  value: string;
  description: string;
}) {

  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm">

      <p className="text-sm text-slate-500">
        {title}
      </p>

      <p className="mt-2 text-2xl font-bold">
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {description}
      </p>

    </div>
  );
}


function Snapshot({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (
    <div className="rounded-xl bg-slate-900 p-4">

      <p className="text-sm text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-2xl font-semibold">
        {value}
      </p>

    </div>
  );
}


function FlowStep({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">

      <div className="flex items-center gap-3">

        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600 text-sm font-bold text-white">
          {number}
        </div>

        <div>

          <p className="font-semibold">
            {title}
          </p>

          <p className="text-xs text-slate-500">
            {text}
          </p>

        </div>

      </div>

    </div>
  );
}


function QuestionItem({
  question,
  score,
  attempts,
  status,
}: {
  question: string;
  score: string;
  attempts: string;
  status: string;
}) {

  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 p-4">

      <div className="min-w-0">

        <p className="truncate font-medium">
          {question}
        </p>

        <p className="mt-1 text-sm text-slate-500">
          {attempts} attempt
          {attempts === "1"
            ? ""
            : "s"}
          {" · "}
          final score {score}
        </p>

      </div>


      <span className="shrink-0 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800">
        {status}
      </span>

    </div>
  );
}


function SummaryBox({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (
    <div className="rounded-xl bg-slate-50 p-3">

      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-sm font-bold">
        {value}
      </p>

    </div>
  );
}


function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (
    <div className="rounded-xl bg-white p-3">

      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 font-semibold">
        {value}
      </p>

    </div>
  );
}


function DecisionBox({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3">

      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 font-semibold">
        {value}
      </p>

    </div>
  );
}


function PlaceholderPage({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {

  return (
    <div className="mx-auto max-w-5xl">

      <div className="rounded-2xl bg-white p-8 shadow-sm">

        <div className="flex items-center gap-3">

          <div className="text-emerald-700">
            {icon}
          </div>

          <h1 className="text-2xl font-bold">
            {title}
          </h1>

        </div>

        <p className="mt-4 text-slate-500">
          {description}
        </p>

      </div>

    </div>
  );
}