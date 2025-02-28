import axios from 'axios';

// Define our data types
export interface Bowler {
  id: number;
  name: string;
  tournaments_played?: number;
  avg_position?: number;
  best_position?: number;
  total_earnings?: number;
  win_percentage?: number;
}

export interface Center {
  id: number;
  name: string;
  location: string;
}

export interface Pattern {
  id: number;
  name: string;
  length: number;
  category: string;
}

export interface Prediction {
  bowlerId: number;
  bowlerName: string;
  predictedPosition: number;
  patternExperience: number;
  centerExperience: number;
  winPercentage: number;
}

export interface PatternPerformance {
  category: string;
  avgPosition: number;
  tournamentCount: number;
  avgEarnings: number;
}

export interface TournamentResult {
  tournamentId: number;
  date: string;
  position: number;
  pattern: string;
}

export interface RadarAttribute {
  attribute: string;
  value: number;
}

export interface BowlerPerformance {
  byPattern: PatternPerformance[];
  recentTrend: TournamentResult[];
  patternRadar: RadarAttribute[];
}

// API Service
const API = {
  // Get list of bowlers
  getBowlers: async (): Promise<Bowler[]> => {
    try {
      const response = await axios.get('/api/bowlers');
      return response.data;
    } catch (error) {
      console.error('Error fetching bowlers:', error);
      return [];
    }
  },

  // Get list of centers
  getCenters: async (): Promise<Center[]> => {
    try {
      const response = await axios.get('/api/centers');
      return response.data;
    } catch (error) {
      console.error('Error fetching centers:', error);
      return [];
    }
  },

  // Get list of patterns
  getPatterns: async (): Promise<Pattern[]> => {
    try {
      const response = await axios.get('/api/patterns');
      return response.data;
    } catch (error) {
      console.error('Error fetching patterns:', error);
      return [];
    }
  },

  // Get predictions for a tournament - handling partial selections
  getPredictions: async (centerId: number, patternId: number): Promise<Prediction[]> => {
    try {
      // Build the query string based on what's selected
      let queryParams = '';
      
      // Only include parameters if they have valid values
      if (centerId && centerId > 0) {
        queryParams += `center=${centerId}`;
      }
      
      if (patternId && patternId > 0) {
        if (queryParams) queryParams += '&';
        queryParams += `pattern=${patternId}`;
      }
      
      // Ensure we have at least one parameter
      if (!queryParams) {
        console.error('No parameters provided for predictions');
        return [];
      }
      
      // Make the API request with the constructed query string
      console.log(`Making prediction request with params: ${queryParams}`);
      const response = await axios.get(`/api/predictions?${queryParams}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching predictions:', error);
      return [];
    }
  },

  // Get detailed performance for a bowler
  getBowlerPerformance: async (bowlerId: number): Promise<BowlerPerformance | null> => {
    try {
      const response = await axios.get(`/api/bowlers/${bowlerId}/performance`);
      return response.data;
    } catch (error) {
      console.error('Error fetching bowler performance:', error);
      return null;
    }
  },

  // Trigger data collection
  collectData: async (years: number[]): Promise<any> => {
    try {
      const response = await axios.post('/api/data/collect', { years });
      return response.data;
    } catch (error) {
      console.error('Error triggering data collection:', error);
      throw error;
    }
  }
};

export default API;