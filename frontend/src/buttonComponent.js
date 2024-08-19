import { greenIconURL, cyanIconURL, newIcon1URL, newIcon2URL } from './svgIcons.js';
import { sharedStatus, subscribe, setIsInTheButton } from './sharedStatus.js';
import { updateFrequenciesFromJson, drawFrequencyTrajectory, clearTrajectoryData } from './frequencyUpdater.js';

let previousStatus = '';

function createImageFromURL(url, onError) {
  const img = new Image();
  img.src = url;
  img.onerror = onError;
  return img;
}

function handleImageLoadError(event) {
  console.error("Failed to load SVG image:", event.target.src);
}

const greenIcon = createImageFromURL(greenIconURL, handleImageLoadError);
const cyanIcon = createImageFromURL(cyanIconURL, handleImageLoadError);
const newIcon1 = createImageFromURL(newIcon1URL, handleImageLoadError);
const newIcon2 = createImageFromURL(newIcon2URL, handleImageLoadError);

let greenIconDimmed = false;
let cyanIconDimmed = false;
let newIcon1Dimmed = false;
let newIcon2Dimmed = false;
let isAudioPlaying = false;

function drawButton(canvas, context, greenIcon, cyanIcon, newIcon1, newIcon2) {
  const buttonWidth = canvas.width * 0.1;
  const buttonHeight = canvas.height * 0.1;

  context.clearRect(10, 10, buttonWidth, buttonHeight);
  context.clearRect(10, canvas.height - 10 - buttonHeight, buttonWidth, buttonHeight);
  context.clearRect(10, canvas.height * 0.33 - buttonHeight / 2, buttonWidth, buttonHeight);
  context.clearRect(10, canvas.height * 0.67 - buttonHeight / 2, buttonWidth, buttonHeight);

  context.globalAlpha = greenIconDimmed ? 0.5 : 1.0;
  context.drawImage(greenIcon, 10, 10, buttonWidth, buttonHeight);

  context.globalAlpha = cyanIconDimmed ? 0.5 : 1.0;
  context.drawImage(cyanIcon, 10, canvas.height - 10 - buttonHeight, buttonWidth, buttonHeight);

  context.globalAlpha = newIcon1Dimmed ? 0.5 : 1.0;
  context.drawImage(newIcon1, 10, canvas.height * 0.33 - buttonHeight / 2, buttonWidth, buttonHeight);

  context.globalAlpha = newIcon2Dimmed ? 0.5 : 1.0;
  context.drawImage(newIcon2, 10, canvas.height * 0.67 - buttonHeight / 2, buttonWidth, buttonHeight);

  context.globalAlpha = 1.0;
}

function isInsideButton(x, y, canvas, buttonX, buttonY, buttonWidth, buttonHeight) {
  const canvasX = x * canvas.width;
  const canvasY = y * canvas.height;
  return canvasX >= buttonX && canvasX <= buttonX + buttonWidth && canvasY >= buttonY && canvasY <= buttonY + buttonHeight;
}

function isInsideGreenButton(x, y, canvas) {
  const buttonWidth = canvas.width * 0.1;
  const buttonHeight = canvas.height * 0.1;
  return isInsideButton(x, y, canvas, 10, 10, buttonWidth, buttonHeight);
}

function isInsideCyanButton(x, y, canvas) {
  const buttonWidth = canvas.width * 0.1;
  const buttonHeight = canvas.height * 0.1;
  const buttonY = canvas.height - 10 - buttonHeight;
  return isInsideButton(x, y, canvas, 10, buttonY, buttonWidth, buttonHeight);
}

function isInsideNewButton1(x, y, canvas) {
  const buttonWidth = canvas.width * 0.1;
  const buttonHeight = canvas.height * 0.1;
  const buttonY = canvas.height * 0.33 - buttonHeight / 2;
  return isInsideButton(x, y, canvas, 10, buttonY, buttonWidth, buttonHeight);
}

function isInsideNewButton2(x, y, canvas) {
  const buttonWidth = canvas.width * 0.1;
  const buttonHeight = canvas.height * 0.1;
  const buttonY = canvas.height * 0.67 - buttonHeight / 2;
  return isInsideButton(x, y, canvas, 10, buttonY, buttonWidth, buttonHeight);
}

function playAudio(url, callback) {
  if (isAudioPlaying) return;
  isAudioPlaying = true;

  fetch(url)
    .then(response => response.blob())
    .then(blob => {
      const audio = new Audio(URL.createObjectURL(blob));
      audio.play().then(() => {
        callback(audio);
      }).catch(error => {
        console.error('Error playing audio file:', error);
        isAudioPlaying = false;
      });
      audio.onended = () => {
        isAudioPlaying = false;
      };
    })
    .catch(error => {
      console.error('Error fetching and playing audio file:', error);
      isAudioPlaying = false;
    });
}

function stopAudio(audio) {
  if (audio) {
    audio.pause();
    audio.currentTime = 0;
    isAudioPlaying = false;
  }
}

function switchAudio(callback) {
  fetch('http://localhost:5000/api/switch-wav-file', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      callback(data.currentIndex);
    })
    .catch(error => console.error('Error switching wav file:', error));
}

function fetchAndUpdateFrequencies(url, canvas, context) {
  fetch(url)
    .then(response => response.json())
    .then(data => {
      clearTrajectoryData(); // 清除旧的轨迹数据
      updateFrequenciesFromJson(data);
      drawFrequencyTrajectory(data, canvas, context);
    })
    .catch(error => {
      console.error('Error fetching JSON file:', error);
    });
}

function handlePositionChange(x, y, status, canvas, context, audio, currentAudioIndex, setCurrentAudioIndex) {
  let isInButton = false;

  if (isInsideGreenButton(x, y, canvas)) {
    isInButton = true;
    if (status === 'StartDrawing') {
      greenIconDimmed = true;
      playAudio(`http://localhost:5000/api/get-wav-file?index=${currentAudioIndex}`, newAudio => audio = newAudio);
    } else if (status === 'EndDrawing' || status === 'NotDrawing') {
      greenIconDimmed = false;
      stopAudio(audio);
    }
  }

  if (isInsideCyanButton(x, y, canvas)) {
    isInButton = true;
    if (status === 'StartDrawing') {
      cyanIconDimmed = true;
    } else if (status === 'EndDrawing' || status === 'NotDrawing') {
      cyanIconDimmed = false;
    }

    if (previousStatus === 'StartDrawing' && status === 'Drawing') {
        switchAudio(newIndex => setCurrentAudioIndex(newIndex));
      }
  
      previousStatus = status;
    }
  
    if (isInsideNewButton1(x, y, canvas)) {
      isInButton = true;
      if (status === 'StartDrawing') {
        newIcon1Dimmed = true;
        playAudio('http://localhost:5000/api/get-pitch-audio', newAudio => audio = newAudio);
      } else if (status === 'EndDrawing' || status === 'NotDrawing') {
        newIcon1Dimmed = false;
        stopAudio(audio);
      }
    }
  
    if (isInsideNewButton2(x, y, canvas)) {
      isInButton = true;
      if (status === 'StartDrawing') {
        newIcon2Dimmed = true;
        fetchAndUpdateFrequencies('http://localhost:5000/api/get-pitch-json', canvas, context);
      } else if (status === 'EndDrawing' || status === 'NotDrawing') {
        newIcon2Dimmed = false;
      }
    }
  
    if (sharedStatus.isInTheButton !== isInButton) {
      setIsInTheButton(isInButton);
    }
  }
  
  export function initializeButton(canvas, context) {
    let audio;
    let currentAudioIndex = 0;
  
    function setCurrentAudioIndex(newIndex) {
      currentAudioIndex = newIndex;
    }
  
    subscribe((status) => {
      if (status.currentStatus === 'StartDrawing' || status.currentStatus === 'Drawing' || status.currentStatus === 'EndDrawing' || status.currentStatus === 'NotDrawing') {
        handlePositionChange(status.currentPosition.x, status.currentPosition.y, status.currentStatus, canvas, context, audio, currentAudioIndex, setCurrentAudioIndex);
        drawButton(canvas, context, greenIcon, cyanIcon, newIcon1, newIcon2);
      }
    });
  
    greenIcon.onload = () => {
      cyanIcon.onload = () => {
        newIcon1.onload = () => {
          newIcon2.onload = () => {
            drawButton(canvas, context, greenIcon, cyanIcon, newIcon1, newIcon2);
          };
        };
      };
    };
  
    greenIcon.onerror = handleImageLoadError;
    cyanIcon.onerror = handleImageLoadError;
    newIcon1.onerror = handleImageLoadError;
    newIcon2.onerror = handleImageLoadError;
  
    return () => drawButton(canvas, context, greenIcon, cyanIcon, newIcon1, newIcon2);
  }
  