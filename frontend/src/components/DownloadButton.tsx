import React, { useState, useRef, useEffect } from 'react';
import { Download, FileText, Image as ImageIcon, FileCode, FileUp } from 'lucide-react';
import { downloadFile, exportToImage, exportToPdf } from '../utils/exportUtils';
import './DownloadButton.css';

interface DownloadButtonProps {
  svgCode: string;
  iterationIndex: number;
}

const DownloadButton: React.FC<DownloadButtonProps> = ({ svgCode, iterationIndex }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fileName = `svg-illustration-v${iterationIndex}`;

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDownload = async (format: 'svg' | 'png' | 'jpeg' | 'pdf' | 'txt') => {
    setIsOpen(false);
    switch (format) {
      case 'svg':
        downloadFile(svgCode, `${fileName}.svg`, 'image/svg+xml');
        break;
      case 'txt':
        downloadFile(svgCode, `${fileName}.txt`, 'text/plain');
        break;
      case 'png':
        await exportToImage(svgCode, 'png', fileName);
        break;
      case 'jpeg':
        await exportToImage(svgCode, 'jpeg', fileName);
        break;
      case 'pdf':
        await exportToPdf(svgCode, fileName);
        break;
    }
  };

  return (
    <div className="download-dropdown" ref={dropdownRef}>
      <button 
        className="download-trigger" 
        onClick={() => setIsOpen(!isOpen)}
        title="Download Illustration"
      >
        <Download size={20} />
        <span>Download</span>
      </button>
      
      {isOpen && (
        <div className="dropdown-menu">
          <button onClick={() => handleDownload('svg')}>
            <FileCode size={16} />
            <span>SVG (Vector)</span>
          </button>
          <button onClick={() => handleDownload('png')}>
            <ImageIcon size={16} />
            <span>PNG (High Res)</span>
          </button>
          <button onClick={() => handleDownload('jpeg')}>
            <ImageIcon size={16} />
            <span>JPEG</span>
          </button>
          <button onClick={() => handleDownload('pdf')}>
            <FileUp size={16} />
            <span>PDF (300 DPI)</span>
          </button>
          <div className="dropdown-divider"></div>
          <button onClick={() => handleDownload('txt')}>
            <FileText size={16} />
            <span>SVG Source (.txt)</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default DownloadButton;
