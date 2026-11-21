use serde::Serialize;
#[cfg(target_os = "linux")]
use std::process::Command;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct LinuxSambaSnapshot {
    config: &'static str,
    usershare: &'static str,
    service: &'static str,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct EnvironmentSnapshot {
    platform: &'static str,
    mode: &'static str,
    file_bridge: &'static str,
    message: &'static str,
    linux_samba: Option<LinuxSambaSnapshot>,
}

#[cfg(target_os = "linux")]
fn command_output(program: &str, args: &[&str]) -> Option<std::process::Output> {
    Command::new(program).args(args).output().ok()
}

#[cfg(target_os = "linux")]
fn service_state() -> &'static str {
    let mut saw_inactive = false;
    for unit in ["smb", "smbd"] {
        if let Some(output) = command_output("systemctl", &["is-active", unit]) {
            match String::from_utf8_lossy(&output.stdout).trim() {
                "active" => return "active",
                "inactive" | "failed" => saw_inactive = true,
                _ => {}
            }
        }
    }
    if saw_inactive {
        "inactive"
    } else {
        "unknown"
    }
}

#[cfg(target_os = "linux")]
fn linux_samba_snapshot() -> LinuxSambaSnapshot {
    let config = match command_output("testparm", &["-s"]) {
        Some(output) if output.status.success() => "valid",
        Some(_) => "invalid",
        None => "missing",
    };
    let usershare = match command_output("net", &["usershare", "list"]) {
        Some(output) if output.status.success() => "accessible",
        Some(output)
            if String::from_utf8_lossy(&output.stderr)
                .to_ascii_lowercase()
                .contains("permission") =>
        {
            "permission_denied"
        }
        Some(_) => "error",
        None => "missing",
    };
    LinuxSambaSnapshot {
        config,
        usershare,
        service: service_state(),
    }
}

#[tauri::command]
fn get_environment_snapshot() -> EnvironmentSnapshot {
    EnvironmentSnapshot {
        platform: std::env::consts::OS,
        mode: "native",
        file_bridge: "unavailable",
        message: "桌面基础框架已启动；SMB 系统集成尚未接入。",
        linux_samba: {
            #[cfg(target_os = "linux")]
            {
                Some(linux_samba_snapshot())
            }
            #[cfg(not(target_os = "linux"))]
            {
                None
            }
        },
    }
}

pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![get_environment_snapshot])
        .run(tauri::generate_context!())
        .expect("failed to start FlowFoundry Desktop");
}
