export interface Dimensions {
  width: number;
  height: number;
}

export interface FitToScreenResult {
  scale: number;
  x: number;
  y: number;
}

export const calculateFitToScreen = (
  container: Dimensions,
  content: Dimensions,
  padding: number = 40
): FitToScreenResult => {
  if (container.width <= 0 || container.height <= 0 || content.width <= 0 || content.height <= 0) {
    return { scale: 1, x: 0, y: 0 };
  }

  const availableWidth = container.width - padding * 2;
  const availableHeight = container.height - padding * 2;

  const scaleX = availableWidth / content.width;
  const scaleY = availableHeight / content.height;

  const scale = Math.min(scaleX, scaleY, 1); // Don't scale up beyond 1:1 if it fits

  // Center the content
  // The animated.div is centered in the viewport using CSS (flex, align-items: center, justify-content: center)
  // So x: 0, y: 0 is already the center. 
  // If we want to ensure it's centered even if scaled, we should return x: 0, y: 0
  // as long as the viewport itself is centered.
  
  return {
    scale,
    x: 0,
    y: 0,
  };
};
