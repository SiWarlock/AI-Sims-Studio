import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { describe, expect, it } from "vitest";
import App from "./App";
import { store } from "./store";

describe("App", () => {
  it("renders the app heading", () => {
    render(
      <Provider store={store}>
        <App />
      </Provider>,
    );
    expect(screen.getByRole("heading", { name: /ai sims creator/i })).toBeInTheDocument();
  });
});
