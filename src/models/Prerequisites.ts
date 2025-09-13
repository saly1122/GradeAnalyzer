export interface Prerequisite {
    id: string;
    title: string;
    description: string;
}

export interface PrerequisiteAnalysis {
    studentId: string;
    prerequisites: Prerequisite[];
}