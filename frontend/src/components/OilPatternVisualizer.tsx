import React, { useState, useEffect } from 'react';

interface OilPatternVisualizerProps {
  patternName?: string;
  length?: number;
  volume?: number;
  ratio?: number;
}

interface PatternData {
  name: string;
  length: number;
  volume: number;
  ratio: number;
  boards: {
    board: number;
    values: {
      distance: number;
      value: number;
    }[];
  }[];
}

const OilPatternVisualizer: React.FC<OilPatternVisualizerProps> = ({ 
  patternName, 
  length, 
  volume, 
  ratio 
}) => {
  const [patternData, setPatternData] = useState<PatternData | null>(null);
  
  // Generate simulated oil pattern data based on length, volume and ratio
  useEffect(() => {
    if (!length) return;
    
    // Default values if not provided
    const oilVolume = volume || 24; // milliliters
    const oilRatio = ratio || 3; // typical house ratio
    
    // Convert feet to boards (1 lane is 39 boards wide)
    const lengthInBoards = Math.floor(length * 12); // 12 inches per foot
    
    // Generate pattern data (simplified simulation)
    const laneWidth = 39;
    const patternValues = [];
    
    for (let board = 0; board < laneWidth; board++) {
      // Calculate oil distribution based on board position and ratio
      // This is a simplified model - real patterns are more complex
      
      // Distance from center of lane (board 20 is center)
      const distFromCenter = Math.abs(board - 19);
      
      // Oil is typically heavier in the middle and gets lighter toward the edges
      // The ratio defines how much more oil is in the middle vs. the edges
      const boardValues = [];
      
      for (let distance = 0; distance < lengthInBoards; distance += 6) {
        // Normalize distance as percentage of total length
        const distancePct = distance / lengthInBoards;
        
        // Oil concentration decreases as you move down the lane
        // It also decreases as you move from center to edges
        // Higher ratio means more difference between center and edges
        const centerFactor = Math.max(0, 1 - (distFromCenter / 19) * (oilRatio / 4));
        const distanceFactor = Math.max(0, 1 - distancePct * 1.2);
        
        // Calculate oil density at this point (0-100 scale)
        let oilDensity = 100 * centerFactor * distanceFactor;
        
        // Simulate pattern type characteristics
        // Long patterns typically have more consistent oil distribution
        if (length > 43) {
          oilDensity = oilDensity * 0.9 + 10; // more flat distribution
        } 
        // Short patterns have more defined "cliff" where oil ends
        else if (length < 37) {
          if (distance > lengthInBoards * 0.75) {
            oilDensity *= 0.4; // sharper dropoff
          }
        }
        
        // Adjust overall oil volume
        oilDensity = oilDensity * (oilVolume / 24);
        
        boardValues.push({
          distance,
          value: Math.min(100, Math.max(0, oilDensity))
        });
      }
      
      patternValues.push({
        board,
        values: boardValues
      });
    }
    
    setPatternData({
      name: patternName || `${length}ft Pattern`,
      length,
      volume: oilVolume,
      ratio: oilRatio,
      boards: patternValues
    });
  }, [patternName, length, volume, ratio]);
  
  if (!patternData) {
    return <div className="flex items-center justify-center h-64">Loading pattern data...</div>;
  }
  
  // Define color gradient for oil density
  const getColor = (value: number): string => {
    // Blue color gradient from light to dark based on oil density
    const intensity = Math.floor(200 - (value * 1.5));
    return `rgb(${intensity}, ${intensity}, 255)`;
  };
  
  return (
    <div className="w-full p-4 bg-white rounded-lg shadow">
      <h2 className="text-xl font-bold mb-2">{patternData.name}</h2>
      <div className="flex gap-4 mb-4 text-sm">
        <div className="px-2 py-1 bg-gray-100 rounded">Length: {patternData.length} ft</div>
        <div className="px-2 py-1 bg-gray-100 rounded">Volume: {patternData.volume} ml</div>
        <div className="px-2 py-1 bg-gray-100 rounded">Ratio: {patternData.ratio}:1</div>
      </div>
      
      <div className="relative overflow-x-auto">
        {/* Lane visualization */}
        <div className="flex flex-col items-center">
          {/* Distance markers */}
          <div className="flex w-full justify-between mb-1 text-xs text-gray-500">
            <span>Foul Line</span>
            <span>{Math.floor(patternData.length * 0.25)}ft</span>
            <span>{Math.floor(patternData.length * 0.5)}ft</span>
            <span>{Math.floor(patternData.length * 0.75)}ft</span>
            <span>{patternData.length}ft</span>
          </div>
          
          {/* Oil pattern visualization */}
          <div className="w-full h-32 bg-yellow-50 border border-gray-300 rounded relative">
            {/* Lane boards */}
            {patternData.boards.map((board) => (
              <div 
                key={`board-${board.board}`}
                className="absolute h-full"
                style={{
                  left: `${(board.board / 39) * 100}%`,
                  width: `${(1/39) * 100}%`,
                }}
              >
                {/* Oil density for this board at different distances */}
                {board.values.map((point, i) => {
                  const nextPoint = board.values[i+1];
                  const width = nextPoint 
                    ? (nextPoint.distance - point.distance) / (patternData.length * 12) * 100
                    : 100 / board.values.length;
                  
                  return (
                    <div
                      key={`point-${board.board}-${point.distance}`}
                      className="absolute h-full"
                      style={{
                        left: `${(point.distance / (patternData.length * 12)) * 100}%`,
                        width: `${width}%`,
                        backgroundColor: getColor(point.value),
                        opacity: point.value / 100
                      }}
                    />
                  );
                })}
              </div>
            ))}
            
            {/* Lane markers */}
            <div className="absolute bottom-0 w-full flex justify-between text-xs px-2">
              <span>1</span>
              <span>10</span>
              <span>20</span>
              <span>30</span>
              <span>39</span>
            </div>
          </div>
          
          {/* Legend */}
          <div className="mt-4 flex items-center text-sm">
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-100 mr-1"></div>
              <span className="mr-4">Light Oil</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-500 mr-1"></div>
              <span className="mr-4">Medium Oil</span>
            </div>
            <div className="flex items-center">
              <div className="w-4 h-4 bg-blue-900 mr-1"></div>
              <span>Heavy Oil</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Pattern characteristics */}
      <div className="mt-4">
        <h3 className="font-semibold mb-1">Pattern Characteristics:</h3>
        <ul className="text-sm pl-5 list-disc">
          {patternData.length < 37 && (
            <>
              <li>Short pattern with pronounced backend reaction</li>
              <li>Typically creates more hook potential at the breakpoint</li>
              <li>Favors angular playing styles and higher rev rates</li>
            </>
          )}
          {patternData.length >= 37 && patternData.length <= 43 && (
            <>
              <li>Medium length pattern with moderate backend reaction</li>
              <li>Balanced oil distribution provides versatility</li>
              <li>Rewards consistent accuracy and adjustability</li>
            </>
          )}
          {patternData.length > 43 && (
            <>
              <li>Long pattern with subdued backend reaction</li>
              <li>More oil volume creates less hook overall</li>
              <li>Favors straighter playing styles and precise accuracy</li>
              <li>Places premium on controlling ball speed and rotation</li>
            </>
          )}
          {patternData.ratio > 4 && (
            <li>Higher ratio creates more defined oil track in center of lane</li>
          )}
          {patternData.ratio < 3 && (
            <li>Lower ratio creates flatter oil distribution across the lane</li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default OilPatternVisualizer;