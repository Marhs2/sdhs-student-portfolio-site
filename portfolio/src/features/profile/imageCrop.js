export const cropDefaults = Object.freeze({
  x: 50,
  y: 50,
  zoom: 1,
});

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

const toNumber = (value, fallback) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
};

export const normalizeCrop = (crop = {}) => ({
  x: clamp(toNumber(crop.x, cropDefaults.x), 0, 100),
  y: clamp(toNumber(crop.y, cropDefaults.y), 0, 100),
  zoom: clamp(toNumber(crop.zoom, cropDefaults.zoom), 1, 2.4),
});

export const getSquareCrop = ({ width, height, crop }) => {
  const normalizedCrop = normalizeCrop(crop);
  const naturalWidth = Math.max(1, Number(width) || 1);
  const naturalHeight = Math.max(1, Number(height) || 1);
  const baseSize = Math.min(naturalWidth, naturalHeight) / normalizedCrop.zoom;
  const maxX = Math.max(0, naturalWidth - baseSize);
  const maxY = Math.max(0, naturalHeight - baseSize);

  return {
    x: maxX * (normalizedCrop.x / 100),
    y: maxY * (normalizedCrop.y / 100),
    size: baseSize,
  };
};

export const getCropPreviewStyle = ({ width, height, crop }) => {
  const naturalWidth = Math.max(1, Number(width) || 1);
  const naturalHeight = Math.max(1, Number(height) || 1);
  const squareCrop = getSquareCrop({ width: naturalWidth, height: naturalHeight, crop });

  return {
    width: `${(naturalWidth / squareCrop.size) * 100}%`,
    height: `${(naturalHeight / squareCrop.size) * 100}%`,
    transform: `translate(${-((squareCrop.x / squareCrop.size) * 100)}%, ${-((squareCrop.y / squareCrop.size) * 100)}%)`,
  };
};
