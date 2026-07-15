// Matches the frozen label set from training/build_labels.py (Ticket 2)
export const ATA_CHAPTERS = {
  '21': 'Air Conditioning / Pressurization / Windows',
  '24': 'Electrical Power',
  '25': 'Equipment / Furnishings',
  '25-EM': 'Emergency Equipment',
  '27': 'Flight Controls',
  '28': 'Fuel',
  '29': 'Hydraulic Power',
  '32': 'Landing Gear',
  '34': 'Navigation',
  '35': 'Oxygen',
  '36': 'Pneumatic',
  '49': 'Airborne Auxiliary Power (APU)',
  '52': 'Doors',
  '71': 'Powerplant / Engine Fuel and Control',
  '78': 'Engine Exhaust',
  '79': 'Oil',
}

// Severity model was reduced to 3 classes (Ticket 5) -- Safety-Critical merged into High
export const SEVERITY_LEVELS = ['Low', 'Medium', 'High']

export const SEVERITY_COLORS = {
  Low: '#3E9C5E',
  Medium: '#D9A404',
  High: '#E0662A',
  'Safety-Critical': '#C4331E', // kept for display of any legacy-labeled data
}

export const LOW_CONFIDENCE_THRESHOLD = 0.4
