export interface Player {
  id: number;
  name: string;
  team: string;
  position: string;
  price: number;
  goals: number;
  assists: number;
  is_active: boolean;
}

export interface FantasyTeam {
  id: number;
  name: string;
  total_points: number;
  max_players: number;
  total_budget: number;
}

export interface TeamPlayer {
  id: number;
  name: string;
  team: string;
  position: string;
  is_captain: boolean;
  is_vice_captain: boolean;
  position_in_team: string;
  price?: number;
}

export interface FantasyTeamDetail {
  team: FantasyTeam;
  players: TeamPlayer[];
  player_count: number;
}

export interface CreateTeamRequest {
  name: string;
}

export interface AddPlayerRequest {
  player_id: number;
}

export interface SetCaptainRequest {
  player_id: number;
  is_vice: boolean;
}

export interface TeamValidation {
  is_valid: boolean;
  errors: string[];
  position_counts: {
    GK: number;
    DEF: number;
    MID: number;
    FWD: number;
  };
  total_players: number;
}
