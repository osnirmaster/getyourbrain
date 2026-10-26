//! Blocking HTTP download for `http-zip` recipe sources.
//!
//! Deliberately small next to `esclient`'s retry loop: that one protects an
//! interactive indexing session against a live server's 429/503 storms; this
//! one fetches a handful of public dump URLs per run. The part worth copying
//! is the SHAPE — bounded attempts, exponential backoff, one-line errors that
//! name the URL and status, and an atomic tmp+rename write so a partial
//! download never exists under the cache's final name.

use std::path::Path;
use std::time::Duration;

use anyhow::{bail, Context, Result};

/// Refuse to buffer more than this on disk. Public advisory dumps are
/// megabytes-to-a-few-hundred-MB; a runaway URL should fail loudly, not fill
/// the disk. Decompression safety is enforced separately at zip-extract time
/// (a small zip can expand enormously — see `source::extract_zip`).
const MAX_DOWNLOAD_BYTES: u64 = 4 << 30;

const ATTEMPTS: u32 = 3;
const INITIAL_BACKOFF: Duration = Duration::from_secs(1);

/// Download `url` to `dest` (atomically). Returns the byte count.
pub fn download(url: &str, dest: &Path) -> Result<u64> {
    let _ = dest;
    // GetYourBrain: build autocontido, `xerj corpus build` não baixa fontes da internet.
    anyhow::bail!("download de {url} desabilitado neste build (GetYourBrain autocontido)")
}

fn once(client: &reqwest::blocking::Client, url: &str, dest: &Path) -> Result<u64> {
    use std::io::{Read, Write};
    let resp = client
        .get(url)
        .send()
        .with_context(|| format!("GET {url}"))?;
    let status = resp.status();
    if !status.is_success() {
        // not retry-worthy in the same way as a timeout, but cheap to retry
        // once upstream hiccuped — the loop above bounds it
        bail!("HTTP {status} for {url}");
    }
    if let Some(len) = resp.content_length() {
        if len > MAX_DOWNLOAD_BYTES {
            bail!("{url} declares {len} bytes, over the {MAX_DOWNLOAD_BYTES} cap");
        }
    }

    let tmp = dest.with_extension("part");
    if let Some(parent) = dest.parent() {
        std::fs::create_dir_all(parent).with_context(|| format!("create {}", parent.display()))?;
    }
    let mut file =
        std::fs::File::create(&tmp).with_context(|| format!("create {}", tmp.display()))?;
    let mut written: u64 = 0;
    // stream: `resp.bytes()` would buffer the entire body in memory before
    // any cap could fire
    let mut reader = resp.take(MAX_DOWNLOAD_BYTES + 1);
    let mut buf = vec![0u8; 64 * 1024];
    loop {
        let n = reader.read(&mut buf)?;
        if n == 0 {
            break;
        }
        written += n as u64;
        if written > MAX_DOWNLOAD_BYTES {
            let _ = std::fs::remove_file(&tmp);
            bail!("{url} exceeded the {MAX_DOWNLOAD_BYTES} download cap");
        }
        file.write_all(&buf[..n])?;
    }
    file.flush()?;
    drop(file);
    std::fs::rename(&tmp, dest).with_context(|| format!("move {} into place", tmp.display()))?;
    Ok(written)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// One canned HTTP response over a raw TcpListener — the fake-node
    /// pattern from `failure_resume_http_tests.rs`. No reqwest server dep.
    /// Owned arguments: the serving thread must be 'static.
    fn serve_once(head: String, body: Vec<u8>) -> std::io::Result<std::net::SocketAddr> {
        let listener = std::net::TcpListener::bind("127.0.0.1:0")?;
        let addr = listener.local_addr()?;
        std::thread::spawn(move || {
            if let Ok((mut sock, _)) = listener.accept() {
                use std::io::{Read, Write};
                let mut buf = [0u8; 1024];
                let _ = sock.read(&mut buf); // discard the request
                let _ = sock.write_all(head.as_bytes());
                let _ = sock.write_all(&body);
                let _ = sock.flush();
            }
        });
        Ok(addr)
    }

    #[test]
    fn downloads_and_retries() {
        let tmp = tempfile::tempdir().unwrap();
        let dest = tmp.path().join("dump.zip");

        // success path
        let addr = serve_once(
            "HTTP/1.1 200 OK\r\nContent-Length: 6\r\nConnection: close\r\n\r\n".to_string(),
            b"hello!".to_vec(),
        )
        .unwrap();
        let n = download(&format!("http://{addr}/x.zip"), &dest).unwrap();
        assert_eq!(n, 6);
        assert_eq!(std::fs::read(&dest).unwrap(), b"hello!");
        assert!(
            !tmp.path().join("dump.part").exists(),
            "no partial left behind"
        );

        // failure path: 404 on every attempt → named error, no dest file
        let addr = serve_once(
            "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".to_string(),
            Vec::new(),
        )
        .unwrap();
        let err = download(&format!("http://{addr}/gone.zip"), &dest)
            .unwrap_err()
            .to_string();
        assert!(err.contains("404"), "{err}");
        assert!(err.contains("3 attempts"), "{err}");
    }
}
