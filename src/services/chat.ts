import { connectDB } from '../db';

export interface ChatMessage {
    from: string; // tg_id
    text: string;
    timestamp: Date;
}

export interface PrivateChat {
    chatId: string;
    user1: string; // tg_id
    user2: string; // tg_id
    messages: ChatMessage[];
}

export class ChatService {
    async createChat(user1: string, user2: string): Promise<string> {
        const db = await connectDB();
        const chatId = `${user1}_${user2}_${Date.now()}`;
        await db.collection('chats').insertOne({ chatId, user1, user2, messages: [] });
        return chatId;
    }

    async getChatsForUser(tg_id: string): Promise<PrivateChat[]> {
        const db = await connectDB();
        return db.collection('chats').find({ $or: [{ user1: tg_id }, { user2: tg_id }] }).toArray();
    }

    async addMessage(chatId: string, from: string, text: string): Promise<void> {
        const db = await connectDB();
        await db.collection('chats').updateOne(
            { chatId },
            { $push: { messages: { from, text, timestamp: new Date() } } }
        );
    }

    async getMessages(chatId: string): Promise<ChatMessage[]> {
        const db = await connectDB();
        const chat = await db.collection('chats').findOne({ chatId });
        return chat ? chat.messages : [];
    }
}
