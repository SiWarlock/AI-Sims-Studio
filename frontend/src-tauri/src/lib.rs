// Phase 0 bootstrap Tauri shell. Sidecar launching and IPC bridging land in
// Task 0.2. For now the app just opens the main window.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|_app| Ok(()))
        .run(tauri::generate_context!())
        .expect("error while running AI Sims Creator");
}
