import { useEffect, useRef } from "react";

type Props = {
  fogDensityPct: number;
  humanDetectionConf: number;
  forwardLidarCm: number;
  thermalTempGradient: number;
};

const WIDTH = 320;
const HEIGHT = 200;

function drawScene(ctx: CanvasRenderingContext2D) {
  const sky = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  sky.addColorStop(0, "#cbd5e1");
  sky.addColorStop(1, "#94a3b8");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, WIDTH, HEIGHT * 0.6);

  ctx.fillStyle = "#475569";
  ctx.fillRect(0, HEIGHT * 0.6, WIDTH, HEIGHT * 0.4);

  ctx.strokeStyle = "#e2e8f0";
  ctx.lineWidth = 3;
  ctx.setLineDash([14, 10]);
  ctx.beginPath();
  ctx.moveTo(WIDTH / 2, HEIGHT);
  ctx.lineTo(WIDTH / 2, HEIGHT * 0.6);
  ctx.stroke();
  ctx.setLineDash([]);
}

function obstaclePosition(forwardLidarCm: number) {
  // Closer obstacle (small lidar distance) draws lower/larger in frame.
  const clamped = Math.max(80, Math.min(1200, forwardLidarCm));
  const depth = 1 - (clamped - 80) / (1200 - 80); // 0 far .. 1 near
  const y = HEIGHT * 0.62 + depth * HEIGHT * 0.28;
  const radius = 10 + depth * 26;
  return { y, radius, depth };
}

function drawOpticalFeed(canvas: HTMLCanvasElement, props: Props) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.clearRect(0, 0, WIDTH, HEIGHT);
  drawScene(ctx);

  const { y, radius } = obstaclePosition(props.forwardLidarCm);
  ctx.fillStyle = "rgba(30,41,59,0.55)";
  ctx.beginPath();
  ctx.ellipse(WIDTH / 2, y, radius * 0.7, radius, 0, 0, Math.PI * 2);
  ctx.fill();

  const fogAlpha = Math.max(0, Math.min(1, props.fogDensityPct / 100));
  const fog = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  fog.addColorStop(0, `rgba(226,232,240,${fogAlpha * 0.55})`);
  fog.addColorStop(1, `rgba(226,232,240,${fogAlpha})`);
  ctx.fillStyle = fog;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
}

function drawThermalView(canvas: HTMLCanvasElement, props: Props) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.clearRect(0, 0, WIDTH, HEIGHT);

  const base = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  base.addColorStop(0, "#0f172a");
  base.addColorStop(1, "#1e293b");
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  const { y, radius } = obstaclePosition(props.forwardLidarCm);
  const confidence = Math.max(0, Math.min(1, props.humanDetectionConf));
  const gradientShift = Math.max(-1, Math.min(1, props.thermalTempGradient / 10));

  const hot = ctx.createRadialGradient(WIDTH / 2, y, 2, WIDTH / 2, y, radius * 2.4);
  const coreColor = gradientShift >= 0 ? "#fef08a" : "#fecaca";
  hot.addColorStop(0, coreColor);
  hot.addColorStop(0.35, "#f97316");
  hot.addColorStop(0.7, "#7c2d12");
  hot.addColorStop(1, "rgba(30,41,59,0)");
  ctx.globalAlpha = 0.35 + confidence * 0.65;
  ctx.fillStyle = hot;
  ctx.beginPath();
  ctx.ellipse(WIDTH / 2, y, radius * 1.6, radius * 2.1, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalAlpha = 1;

  if (confidence > 0.4) {
    ctx.strokeStyle = "#facc15";
    ctx.lineWidth = 2;
    ctx.strokeRect(WIDTH / 2 - radius * 1.2, y - radius * 1.6, radius * 2.4, radius * 3.1);
    ctx.fillStyle = "#facc15";
    ctx.font = "bold 11px system-ui, sans-serif";
    ctx.fillText(`${Math.round(confidence * 100)}%`, WIDTH / 2 - radius * 1.2, y - radius * 1.6 - 6);
  }
}

export function ThermalUpscalingCanvas(props: Props) {
  const opticalRef = useRef<HTMLCanvasElement>(null);
  const thermalRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (opticalRef.current) drawOpticalFeed(opticalRef.current, props);
    if (thermalRef.current) drawThermalView(thermalRef.current, props);
  }, [props.fogDensityPct, props.humanDetectionConf, props.forwardLidarCm, props.thermalTempGradient]);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-panel">
      <h2 className="mb-3 text-base font-bold text-slate-900">Edge-AI thermal upscaling</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <div className="mb-2 text-xs font-semibold text-slate-500">What the truck driver sees in fog (blinded optical feed)</div>
          <canvas ref={opticalRef} width={WIDTH} height={HEIGHT} className="w-full rounded-lg border border-slate-200" />
        </div>
        <div>
          <div className="mb-2 text-xs font-semibold text-slate-500">What Third Eye reveals (upscaled thermal view)</div>
          <canvas ref={thermalRef} width={WIDTH} height={HEIGHT} className="w-full rounded-lg border border-slate-200" />
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        Illustrative rendering driven by live telemetry (fog density, forward LiDAR range, human-detection confidence,
        thermal gradient). Not a physical camera or thermal sensor feed.
      </p>
    </div>
  );
}
