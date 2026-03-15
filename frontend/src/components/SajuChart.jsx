import React from 'react';

const Pillar = ({ label, data }) => {
  if (!data) return <div className="pillar empty">...</div>;
  
  const ganji = data.ganji; 
  const stem = ganji[0];
  const branch = ganji[1];
  
  // Element to CSS Variable map
  const elementColorMap = {
    "Wood": "var(--wood)",
    "Fire": "var(--fire)",
    "Earth": "var(--earth)",
    "Metal": "var(--metal)",
    "Water": "var(--water)"
  };

  return (
    <div className="pillar">
      <div className="pillar-header">{label}</div>
      <div className="char-box" style={{ backgroundColor: elementColorMap[data.element] }}>
        <span className="char">{stem}</span>
      </div>
      <div className="char-box" style={{ backgroundColor: elementColorMap[data.element] }}>
        <span className="char">{branch}</span>
      </div>
    </div>
  );
};

const SajuChart = ({ data }) => {
  if (!data) return null;

  return (
    <div className="saju-chart">
      <h2>분석 결과</h2>
      <div className="pillars-container">
        <Pillar label="시" data={data.hour} />
        <Pillar label="일" data={data.day} />
        <Pillar label="월" data={data.month} />
        <Pillar label="연" data={data.year} />
      </div>
      <div className="analysis-text">
        <p>당신은 <strong>{data.day.element}</strong>의 기운을 타고난 {data.day.ganji}일생입니다.</p>
      </div>
    </div>
  );
};

export default SajuChart;
