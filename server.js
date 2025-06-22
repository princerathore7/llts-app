// LLTS Server - Final Working Version

const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = process.env.PORT || 5000;
const JWT_SECRET = process.env.JWT_SECRET || 'llts_secret_key';

// Middleware
app.use(cors());
app.use(express.json()); // built-in JSON parser

// MongoDB connection
mongoose.connect(
  'mongodb+srv://prince242com:prince242%24@cluster0.3k2ajwh.mongodb.net/LLTS?retryWrites=true&w=majority&appName=Cluster0',
  {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    serverSelectionTimeoutMS: 10000
  }
).then(() => {
  console.log('MongoDB Connected');
}).catch((err) => {
  console.error('MongoDB Connection Error:', err);
});

// User schema
const userSchema = new mongoose.Schema({
  username: { type: String, unique: true, sparse: true },
  password: String,
  role: String, // owner or worker
  name: String,
  email: String,
  skills: [String],
  experience: Number
});

const User = mongoose.model('User', userSchema);

// Tender schema
const tenderSchema = new mongoose.Schema({
  title: String,
  description: String,
  location: String,
  ownerId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  budget: Number,
  deadline: String,
  createdAt: { type: Date, default: Date.now }
});

const Tender = mongoose.model('Tender', tenderSchema);

// Owner Signup
app.post('/owner/signup', async (req, res) => {
  const { username, password, name, email } = req.body;
  if (!username || !password || !name || !email) {
    return res.status(400).json({ message: 'Please provide all required fields.' });
  }
  try {
    const existingUser = await User.findOne({ $or: [{ username }, { email }] });
    if (existingUser) return res.status(400).json({ message: 'User already exists' });

    const hashedPassword = await bcrypt.hash(password, 10);

    const newUser = new User({
      username,
      password: hashedPassword,
      role: 'owner',
      name,
      email
    });

    await newUser.save();

    const token = jwt.sign({ id: newUser._id, role: newUser.role }, JWT_SECRET, { expiresIn: '2h' });

    res.status(201).json({
      message: 'Owner signup successful',
      role: newUser.role,
      token
    });
  } catch (err) {
    console.error('Owner signup error:', err);
    res.status(500).json({ message: 'Server error during owner signup' });
  }
});

// Worker Signup
app.post('/worker/signup', async (req, res) => {
  const { username, password, name, skills, experience } = req.body;
  if (!username || !password || !name) {
    return res.status(400).json({ message: 'Please provide all required fields.' });
  }
  try {
    const existingUser = await User.findOne({ username });
    if (existingUser) return res.status(400).json({ message: 'Worker already exists' });

    const hashedPassword = await bcrypt.hash(password, 10);

    const newUser = new User({
      username,
      password: hashedPassword,
      role: 'worker',
      name,
      skills,
      experience
    });

    await newUser.save();

    const token = jwt.sign({ id: newUser._id, role: newUser.role }, JWT_SECRET, { expiresIn: '2h' });

    res.status(201).json({
      message: 'Worker signup successful',
      role: newUser.role,
      token
    });
  } catch (err) {
    console.error('Worker signup error:', err);
    res.status(500).json({ message: 'Server error during worker signup' });
  }
});

// Owner Login
app.post('/owner/login', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ message: 'Please provide username and password.' });
  }
  try {
    const user = await User.findOne({ username, role: 'owner' });
    if (!user) return res.status(400).json({ message: 'Invalid username or password' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(400).json({ message: 'Invalid username or password' });

    const token = jwt.sign({ id: user._id, role: user.role }, JWT_SECRET, { expiresIn: '2h' });

    res.status(200).json({
      message: 'Owner login successful',
      token,
      role: user.role
    });
  } catch (err) {
    console.error('Owner login error:', err);
    res.status(500).json({ message: 'Server error during owner login' });
  }
});

// Worker Login
app.post('/worker/login', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.status(400).json({ message: 'Please provide username and password.' });
  }
  try {
    const user = await User.findOne({ username, role: 'worker' });
    if (!user) return res.status(400).json({ message: 'Invalid username or password' });

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return res.status(400).json({ message: 'Invalid username or password' });

    const token = jwt.sign({ id: user._id, role: user.role }, JWT_SECRET, { expiresIn: '2h' });

    res.status(200).json({
      message: 'Worker login successful',
      token,
      role: user.role
    });
  } catch (err) {
    console.error('Worker login error:', err);
    res.status(500).json({ message: 'Server error during worker login' });
  }
});

// Post Tender
app.post('/api/tenders', async (req, res) => {
  try {
    const { title, description, location, budget, deadline, ownerId } = req.body;
    if (!ownerId) return res.status(400).json({ message: 'Owner ID required' });

    const newTender = new Tender({ title, description, location, budget, deadline, ownerId });
    await newTender.save();

    res.status(201).json({ message: 'Tender posted successfully' });
  } catch (err) {
    console.error('Error posting tender:', err);
    res.status(500).json({ message: 'Error posting tender' });
  }
});

// Get All Tenders
app.get('/api/tenders', async (req, res) => {
  try {
    const tenders = await Tender.find().populate('ownerId', 'name username');
    res.status(200).json(tenders);
  } catch (err) {
    console.error('Error fetching tenders:', err);
    res.status(500).json({ message: 'Error fetching tenders' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
