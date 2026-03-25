/**
 * SVG Export Utility
 */

export const downloadFile = (content: string, fileName: string, contentType: string) => {
  const a = document.createElement('a');
  const file = new Blob([content], { type: contentType });
  a.href = URL.createObjectURL(file);
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(a.href);
};

export const exportToImage = async (svgCode: string, format: 'png' | 'jpeg', fileName: string) => {
  const svg = new Blob([svgCode], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(svg);
  
  const img = new Image();
  img.src = url;
  
  await new Promise((resolve) => {
    img.onload = resolve;
  });

  const canvas = document.createElement('canvas');
  // Use a higher resolution for high quality (e.g. 2x or 3x)
  const scale = 3; 
  
  // Extract width/height from SVG or use defaults
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgCode, 'image/svg+xml');
  const svgEl = doc.querySelector('svg');
  
  let width = 800;
  let height = 600;
  
  if (svgEl) {
    if (svgEl.viewBox.baseVal.width) {
      width = svgEl.viewBox.baseVal.width;
      height = svgEl.viewBox.baseVal.height;
    } else if (svgEl.width.baseVal.value) {
      width = svgEl.width.baseVal.value;
      height = svgEl.height.baseVal.value;
    }
  }

  canvas.width = width * scale;
  canvas.height = height * scale;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  if (format === 'jpeg') {
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
  
  ctx.scale(scale, scale);
  ctx.drawImage(img, 0, 0, width, height);
  
  const dataUrl = canvas.toDataURL(`image/${format}`, 1.0);
  const link = document.createElement('a');
  link.download = `${fileName}.${format}`;
  link.href = dataUrl;
  link.click();
  
  URL.revokeObjectURL(url);
};

export const exportToPdf = async (svgCode: string, fileName: string) => {
  // Simple PDF export using browser print if library is not available
  // Or we can try to use a simple approach with an iframe
  const printWindow = window.open('', '_blank');
  if (!printWindow) return;
  
  printWindow.document.write(`
    <html>
      <head>
        <title>Export PDF</title>
        <style>
          body { margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; }
          svg { width: 100%; height: auto; }
          @page { size: auto; margin: 0; }
        </style>
      </head>
      <body>
        ${svgCode}
        <script>
          window.onload = () => {
            window.print();
            window.close();
          };
        </script>
      </body>
    </html>
  `);
  printWindow.document.close();
};
