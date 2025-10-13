import { MongoClient, Db } from 'mongodb';
import process from 'process';

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/anon_board';

let client: MongoClient;
let db: Db;

export async function connectDB(): Promise<Db> {
    if (!client) {
        client = new MongoClient(MONGO_URI);
        await client.connect();
        db = client.db();
    }
    return db;
}

export async function disconnectDB(): Promise<void> {
    if (client) {
        await client.close();
    }
}
