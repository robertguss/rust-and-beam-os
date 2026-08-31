use std::env;
use std::process::ExitCode;

const PLACEHOLDERS: &[&str] = &[
    "build-kernel",
    "build-otp",
    "build-release",
    "image",
    "run-headless",
    "run-gui",
    "test-qemu",
];

fn main() -> ExitCode {
    let mut args = env::args().skip(1);
    match (args.next().as_deref(), args.next()) {
        (None | Some("help"), None) => {
            print_help();
            ExitCode::SUCCESS
        }
        (Some("status"), None) => {
            println!("Phase 0 repository scaffold is active.");
            println!("Unavailable commands: {}", PLACEHOLDERS.join(", "));
            println!("Use `just --list` to inspect their visible command lines.");
            ExitCode::SUCCESS
        }
        (Some("unavailable"), Some(command)) if PLACEHOLDERS.contains(&command.as_str()) => {
            eprintln!(
                "xtask: `{command}` is intentionally unavailable until its owning plan task is ready"
            );
            ExitCode::from(2)
        }
        _ => {
            eprintln!("xtask: unknown command or arguments\n");
            print_help();
            ExitCode::from(2)
        }
    }
}

fn print_help() {
    println!("Usage: cargo xtask <help|status|unavailable COMMAND>");
    println!("Build and image commands remain fail-loud placeholders in RB-T-P001.");
}
