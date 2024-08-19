// src/frequencyUpdater.js

import { setMinFrequency, setMaxFrequency } from './sharedStatus.js';

let trajectoryData = [];

export function updateFrequenciesFromJson(jsonData) {
  const { max_frequency, min_frequency } = jsonData;

  // 更新 sharedStatus 中的频率范围
  setMinFrequency(min_frequency);
  setMaxFrequency(max_frequency);

  // 记录频率范围的变化
  console.log(`Frequency range updated: min_frequency = ${min_frequency}, max_frequency = ${max_frequency}`);
}

export function clearTrajectoryData() {
  trajectoryData = [];
}

export function drawFrequencyTrajectory(jsonData, canvas, context) {
  const { data, max_frequency, min_frequency } = jsonData;

  const xMin = canvas.width * 0.15;
  const xMax = canvas.width * 0.95;
  const yMin = canvas.height * 0.1;
  const yMax = canvas.height * 0.9;

  context.strokeStyle = 'rgba(128, 128, 128, 0.5)';
  context.lineWidth = 100;  // 增加线的粗细
  context.beginPath();

  let isDrawing = false;
  let trajectorySegment = [];

  data.forEach(point => {
    const { time, frequency } = point;
    if (frequency !== "NaN") {
      const x = xMin + (xMax - xMin) * time;
      const y = yMin + (yMax - yMin) * (1 - (Math.log(frequency) - Math.log(min_frequency)) / (Math.log(max_frequency) - Math.log(min_frequency)));

      if (isDrawing) {
        context.lineTo(x, y);
        trajectorySegment.push({ x, y });
      } else {
        context.moveTo(x, y);
        isDrawing = true;
        trajectorySegment.push({ x, y });
      }
    } else {
      if (isDrawing) {
        trajectoryData.push(trajectorySegment);
        trajectorySegment = [];
      }
      isDrawing = false;
    }
  });

  if (trajectorySegment.length > 0) {
    trajectoryData.push(trajectorySegment);
  }

  context.stroke();
}

export function getTrajectoryData() {
  return trajectoryData;
}
