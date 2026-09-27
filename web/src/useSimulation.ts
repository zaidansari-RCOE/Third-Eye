import { useCallback, useEffect, useRef, useState } from "react";
import { getControlRoom, getHealth, getMap, parseEnvelope, websocketUrl } from "./api";
import type { ConnectionStatus, ControlRoomSnapshot, MapDocument } from "./types";

const MAX_BACKOFF_MS = 8000;

export function useSimulation() {
  const [snapshot, setSnapshot] = useState<ControlRoomSnapshot | null>(null);
  const [map, setMap] = useState<MapDocument | null>(null);
  const [connection, setConnection] = useState<ConnectionStatus>("connecting");
  const [commandError, setCommandError] = useState<string | null>(null);
  const snapshotRef = useRef<ControlRoomSnapshot | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const stoppedRef = useRef(false);

  useEffect(() => {
    snapshotRef.current = snapshot;
  }, [snapshot]);

  useEffect(() => {
    let cancelled = false;
    getMap()
      .then((document) => {
        if (!cancelled) setMap(document);
      })
      .catch(() => {
        /* health/ws will surface disconnect */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    stoppedRef.current = false;
    let timer: number | undefined;

    const connect = () => {
      if (stoppedRef.current) return;
      setConnection(retriesRef.current === 0 ? "connecting" : "reconnecting");
      const socket = new WebSocket(websocketUrl());
      socketRef.current = socket;
      socket.onopen = () => {
        retriesRef.current = 0;
        setConnection("live");
        void getHealth().catch(() => undefined);
      };
      socket.onmessage = (event) => {
        try {
          const message = parseEnvelope(String(event.data));
          if (message.type === "control_room_snapshot" && message.payload) {
            setSnapshot(message.payload);
          }
        } catch {
          /* ignore malformed frames; keep last snapshot */
        }
      };
      socket.onerror = () => {
        socket.close();
      };
      socket.onclose = () => {
        if (stoppedRef.current) return;
        setConnection("disconnected");
        const delay = Math.min(500 * 2 ** retriesRef.current, MAX_BACKOFF_MS);
        retriesRef.current += 1;
        timer = window.setTimeout(connect, delay);
      };
    };

    void getControlRoom()
      .then((payload) => setSnapshot(payload))
      .catch(() => undefined)
      .finally(() => {
        if (!stoppedRef.current) connect();
      });

    const healthTimer = window.setInterval(() => {
      void getHealth().catch(() => {
        if (socketRef.current?.readyState !== WebSocket.OPEN) {
          setConnection((current) => (current === "live" ? "reconnecting" : current));
        }
      });
    }, 5000);

    return () => {
      stoppedRef.current = true;
      window.clearInterval(healthTimer);
      if (timer !== undefined) window.clearTimeout(timer);
      socketRef.current?.close();
    };
  }, []);

  const runCommand = useCallback(async (action: () => Promise<unknown>) => {
    setCommandError(null);
    try {
      await action();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Command failed";
      setCommandError(message);
      throw error;
    }
  }, []);

  return { snapshot, map, connection, commandError, setCommandError, runCommand };
}
