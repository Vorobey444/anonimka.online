import { connectDB } from '../db';
import { ObjectId } from 'mongodb';

export interface Ad {
    id: string;
    title: string;
    description: string;
    userId: string;
    createdAt: Date;
}

export class AdsService {
    public async createAd(title: string, description: string, userId: string): Promise<Ad> {
        const db = await connectDB();
        const ad: Ad = {
            id: new ObjectId().toString(),
            title,
            description,
            userId,
            createdAt: new Date(),
        };
        await db.collection('ads').insertOne(ad);
        return ad;
    }

    public async getAds(): Promise<Ad[]> {
        const db = await connectDB();
        return db.collection('ads').find().sort({ createdAt: -1 }).limit(50).toArray();
    }

    public async getAdById(id: string): Promise<Ad | null> {
        const db = await connectDB();
        return db.collection('ads').findOne({ id });
    }

    public async deleteAd(id: string): Promise<boolean> {
        const db = await connectDB();
        const result = await db.collection('ads').deleteOne({ id });
        return result.deletedCount === 1;
    }
}
}