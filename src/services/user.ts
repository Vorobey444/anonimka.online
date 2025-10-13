import { connectDB } from '../db';

export interface User {
    tg_id: string;
    nickname: string;
}

export class UserService {
    async registerNickname(tg_id: string, nickname: string): Promise<boolean> {
        const db = await connectDB();
        const exists = await db.collection('users').findOne({ nickname });
        if (exists) return false;
        await db.collection('users').insertOne({ tg_id, nickname });
        return true;
    }

    async getNickname(tg_id: string): Promise<string | null> {
        const db = await connectDB();
        const user = await db.collection('users').findOne({ tg_id });
        return user ? user.nickname : null;
    }

    async isNicknameTaken(nickname: string): Promise<boolean> {
        const db = await connectDB();
        const exists = await db.collection('users').findOne({ nickname });
        return !!exists;
    }
}
