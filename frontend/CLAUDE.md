# Frontend — Claude Code Guidance

You are working inside `frontend/`. This is the Tauri v2 host + React + Redux Toolkit + Tailwind frontend.

## Stack

- **Tauri v2** (Rust host, system webview)
- **React 18** (function components only)
- **TypeScript strict** (zero `any`, zero `tsc` errors)
- **Redux Toolkit** for state
- **React Router v6** in memory mode (not browser mode)
- **Tailwind CSS** for styling, Radix UI for accessible primitives
- **Vite** for builds

Reminder: `CODING_STANDARDS.md` at the repo root has the full style and quality rules. This file covers patterns specific to frontend work.

## Layout

```
frontend/
├── src/
│   ├── main.tsx                    # Vite entry, mounts <App>
│   ├── App.tsx                     # Router + Provider wrapper
│   ├── store/
│   │   ├── index.ts                # store config
│   │   └── slices/                 # one file per slice (see below)
│   ├── screens/                    # one file per top-level screen
│   ├── components/                 # reusable components, one folder each
│   ├── ipc/                        # IPC client, event subscribers
│   ├── hooks/                      # shared hooks
│   ├── styles/                     # global Tailwind config additions
│   └── lib/                        # pure utilities (no JSX, no state)
├── src-tauri/                      # Tauri Rust shell (rarely touched)
└── package.json
```

## Redux Slice Conventions

One slice per feature (see `docs/tad/01-component-architecture.md` §3.1.2 for the full list: project, generation, ui, templates, config, logs, archetypes).

### Slice file structure

```tsx
// frontend/src/store/slices/projectSlice.ts
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { Project } from "shared-types";

interface ProjectState {
  current: Project | null;
  recentProjects: Project[];
  loading: boolean;
  error: string | null;
}

const initialState: ProjectState = {
  current: null,
  recentProjects: [],
  loading: false,
  error: null,
};

const projectSlice = createSlice({
  name: "project",
  initialState,
  reducers: {
    setCurrentProject(state, action: PayloadAction<Project>) {
      state.current = action.payload;
    },
    // ... other reducers
  },
});

export const { setCurrentProject } = projectSlice.actions;
export default projectSlice.reducer;

// Selectors live in the same file
export const selectCurrentProject = (s: RootState) => s.project.current;
```

### Async thunks

For any IPC call:

```tsx
export const openProject = createAsyncThunk<Project, string>(
  "project/open",
  async (projectId, { rejectWithValue }) => {
    try {
      return await ipc.request("project.open", { project_id: projectId });
    } catch (err) {
      return rejectWithValue(errorFromIPC(err));
    }
  }
);
```

Handle lifecycle in `extraReducers`, not manually in the component.

### No cross-slice imports

If two slices need to coordinate, either:
1. Use middleware to react to actions from another slice
2. Or they should be one slice

Never `import { foo } from "../otherSlice"` inside a slice.

## IPC Client Pattern

The IPC client is the sole owner of the sidecar connection. Components never talk to it directly for subscriptions — subscriptions flow through Redux.

```tsx
// frontend/src/ipc/client.ts
class IPCClient {
  async request<TParams, TResult>(method: string, params: TParams): Promise<TResult> { ... }
  subscribe(eventType: string, handler: (params: unknown) => void): () => void { ... }
}
export const ipc = new IPCClient();
```

For requests: components dispatch async thunks, which call `ipc.request`.

For push events: a top-level `IPCEventsListener` component (mounted in `App.tsx`) subscribes to every event type and dispatches typed Redux actions.

Never call `ipc.request` from inside a component body. Always via a thunk.

## Types from `shared-types/`

Types for any data crossing the IPC boundary come from `shared-types/`, which is auto-generated from the Python Pydantic schemas.

```tsx
import type { Project, Collection, ItemStatus } from "shared-types";
```

Do not hand-write these types even as quick placeholders. Run `npm run gen:types` (which calls `python scripts/generate_types.py`) if they are missing.

## Component Conventions

### Component files

```tsx
// frontend/src/components/CollectionBoard/CollectionBoard.tsx
import { useSelector, useDispatch } from "react-redux";
import type { FC } from "react";
// ... imports

interface CollectionBoardProps {
  collectionId: string;
}

const CollectionBoard: FC<CollectionBoardProps> = ({ collectionId }) => {
  // hooks first
  const items = useSelector(selectItemsForCollection(collectionId));
  // ...

  // then render
  return (
    <div className="grid grid-cols-3 gap-4 p-6">
      {items.map((item) => (
        <ItemCard key={item.id} item={item} />
      ))}
    </div>
  );
};

export default CollectionBoard;
```

### Component rules

- **One component per file** (plus small internal subcomponents that aren't exported).
- **Props interface is exported** if any other file might extend it.
- **Default export for the component itself.**
- **No component exceeds ~300 lines.** Split when longer.
- **No logic in JSX beyond trivial conditionals and maps.** Extract to hooks or functions.

## Tailwind Usage

- **Utility-first.** Most styling is Tailwind classes directly in JSX.
- **Component-scoped classes use `@apply`** sparingly in CSS modules.
- **No custom colors outside `tailwind.config.js`.** Semantic color names from the config.
- **Responsive breakpoints from the config.** Don't hand-author media queries.
- **Accessibility classes (`focus:`, `hover:`, `aria-*`) are non-negotiable** on interactive elements.

## Routing

Memory router, not browser router. Route paths are internal app concepts, not URLs users see.

```tsx
// frontend/src/App.tsx
import { createMemoryRouter, RouterProvider } from "react-router-dom";

const router = createMemoryRouter([
  { path: "/", element: <HomeScreen /> },
  { path: "/project/:id", element: <ProjectRoot /> },
  { path: "/admin/*", element: <AdminModeGate /> },
  // ...
]);
```

Admin mode routes are wrapped in `<AdminModeGate>` which checks the Redux `ui.adminModeActive` flag.

## Testing

- **vitest + React Testing Library.**
- Test files live next to the component: `CollectionBoard/CollectionBoard.test.tsx`.
- Query by role/label: `screen.getByRole("button", { name: /generate/i })`.
- Mock the IPC client via `vi.mock("../../ipc/client")` with canned responses.
- Never test internal state directly. Test user-visible behavior.

## Common Tasks

- **New screen:** add to `src/screens/`, route in `App.tsx`, optionally a slice action for "active screen."
- **New reusable component:** add to `src/components/{Name}/` with `{Name}.tsx`, `{Name}.test.tsx`, optional `{Name}.module.css`.
- **New IPC method consumption:** add a thunk in the appropriate slice, handle the three lifecycle cases (pending/fulfilled/rejected).
- **New notification handler:** add to `IPCEventsListener` in `src/ipc/events.ts`, dispatch the corresponding slice action.

## Load These Docs When...

- Implementing a screen: `docs/prd/08-non-functional-and-workflows.md` (§20 screens) + `docs/tad/01-component-architecture.md` (§3.1)
- Adding IPC: the `docs/api/{namespace}.md` shard for that namespace
- State management patterns: this file is authoritative; `docs/tad/01-component-architecture.md` §3.1.2 lists the slices
- Styling the app: `docs/prd/05-content-and-style.md` for visual style principles (user-facing content is semi-Alpha; the app UI itself is maintainer-defined)
