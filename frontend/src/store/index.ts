import { configureStore, createSlice } from "@reduxjs/toolkit";

// Phase 0 bootstrap — real slices (project, generation, ui, templates, config,
// logs, archetypes) are added from Task 0.5 (project storage) onward. This
// placeholder slice exists so the store has at least one reducer; Redux Toolkit
// warns on an empty reducer map.
const bootstrapSlice = createSlice({
  name: "_bootstrap",
  initialState: { phase: 0 as const },
  reducers: {},
});

export const store = configureStore({
  reducer: {
    _bootstrap: bootstrapSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
