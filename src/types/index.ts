export interface Ad {
    id: string;
    title: string;
    description: string;
    userId: string;
    createdAt: Date;
}

export interface User {
    id: string;
    username: string;
    firstName?: string;
    lastName?: string;
    createdAt: Date;
}