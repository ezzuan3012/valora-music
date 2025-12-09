from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import random
import time
from datetime import timedelta 

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

# --- Configuration ---
# the client id will be set via environment variables for security
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SCOPE = 'user-library-read playlist-modify-public playlist-modify-private'

# Check to make sure they loaded correctly
if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("🚨 ERROR: SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET is missing from environment variables!")

# Update this to your Render URL when pushing to live, 
# or keep as localhost for testing on your computer.
REDIRECT_URI = "https://valora-music-project.onrender.com/callback"

# --- 1. Load Processed Song Database (The "Brain") ---
DATABASE_FILE = 'valora_database.csv' 
try:
    print(f"Loading recommendation database: {DATABASE_FILE}...")
    df_db = pd.read_csv(DATABASE_FILE)
    df_db['app_mood'] = df_db['app_mood'].astype('category')
    df_db['artist_simple'] = df_db['artists'].astype(str).str.lower().str.split(';').str[0].str.split(',').str[0]
    print(f"✅ Recommendation database loaded ({len(df_db)} tracks).")
except FileNotFoundError:
    print(f"🚨 FATAL ERROR: Could not find '{DATABASE_FILE}'.")
    print("Please run 'process_final_database.py' first.")
    exit()

# --- 2. Load Liked Songs Database (For Personalization) ---
LIKED_SONGS_FILE = 'Liked_Songs_Spotify.csv'
try:
    df_liked = pd.read_csv(LIKED_SONGS_FILE)
    liked_song_ids = set(df_liked['Track URI'].str.split(':').str[2])
    print(f"✅ Loaded {len(liked_song_ids)} liked song IDs from CSV.")
except Exception:
    print(f"Warning: '{LIKED_SONGS_FILE}' not found or invalid. Personalization will be limited.")
    liked_song_ids = set()

# --- Spotify Authentication Setup ---
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID, 
        client_secret=CLIENT_SECRET, 
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )
sp_oauth = create_spotify_oauth()

def get_spotify_client():
    token_info = session.get('token_info', None)
    if not token_info: return None, True
    now = int(time.time()); is_expired = token_info.get('expires_at', 0) - now < 60
    if is_expired:
        try:
            token_info = sp_oauth.refresh_access_token(token_info.get('refresh_token'))
            session['token_info'] = token_info
        except Exception as e: 
            print(f"Error refreshing token: {e}"); session.clear(); return None, True
    try:
        sp = spotipy.Spotify(auth=token_info.get('access_token'))
        sp.current_user(); return sp, False
    except Exception as e: 
        print(f"Error creating user client: {e}"); session.clear(); return None, True

def get_spotify_client_credentials():
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        return spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    except Exception as e: 
        print(f"Error creating client credentials client: {e}"); return None

# --- Flask Routes ---
@app.route('/')
def index():
    # --- THIS IS CHANGED ---
    # If user is already logged in, send them to remarks
    if 'token_info' in session:
        return redirect(url_for('remarks'))
    
    # Otherwise, show the login page
    return render_template('index.html')

@app.route('/login')
def login(): return redirect(sp_oauth.get_authorize_url())

@app.route('/callback')
def callback():
    session.clear(); code = request.args.get('code')
    session.permanent = True
    try:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        session['token_info'] = token_info
        # --- THIS IS CHANGED ---
        # Redirect to remarks page after login
        return redirect(url_for('remarks'))
    except Exception as e: 
        print(f"Error in callback: {e}"); return redirect(url_for('index'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/remarks')
def remarks():
    # Check if user is logged in (has a token in their session)
    if 'token_info' not in session:
        # If not, send them back to the login page
        return redirect(url_for('index'))
    
    # If they are logged in, show them the remarks page
    return render_template('remarks.html')

@app.route('/questionnaire')
def questionnaire():
    sp, needs_redirect = get_spotify_client()
    if needs_redirect: return redirect(url_for('index'))
    return render_template('questionnaire.html')

@app.route('/recommendations')
def recommendations():
    sp, needs_redirect = get_spotify_client()
    if needs_redirect: return redirect(url_for('index'))
    user_mood = request.args.get('mood')
    if not user_mood: return redirect(url_for('questionnaire'))
        
    mood_classes = {
        "Happy/Energetic": "bg-happy",
        "Angry/Tense": "bg-angry",
        "Sad/Melancholy": "bg-sad",
        "Calm/Peaceful": "bg-calm"
    }
    mood_class = mood_classes.get(user_mood, 'bg-default') 

    return render_template('recommendations.html', mood=user_mood, mood_class=mood_class)

# --- API: Get Recommendations ---
@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    print("--- Received request at /get_recommendations ---")
    sp_user, needs_redirect = get_spotify_client()
    if needs_redirect: return jsonify({'error': 'User not logged in', 'login_required': True}), 401
    
    try:
        data = request.get_json()
        user_mood = data.get('mood')
        
        if not user_mood: return jsonify({'error': 'Mood not provided'}), 400
        print(f"Target mood: {user_mood}")

        mood_filtered_songs = df_db[df_db['app_mood'] == user_mood]
        
        if mood_filtered_songs.empty:
            return jsonify({'recommendations': [], 'message': f'No songs found for mood "{user_mood}".'})
        
        user_liked_ids = liked_song_ids.copy() 
        try:
            saved_tracks = sp_user.current_user_saved_tracks(limit=50)
            user_liked_ids.update([item['track']['id'] for item in saved_tracks['items']])
            print(f"Personalizing with {len(user_liked_ids)} total liked songs.")
        except Exception as e:
            print(f"Warning: Could not get user's live liked songs: {e}.")

        matches_liked = mood_filtered_songs[mood_filtered_songs['track_id'].isin(user_liked_ids)]
        num_liked = min(len(matches_liked), 8) 
        liked_recs = matches_liked.sample(n=num_liked)
        
        final_track_ids = list(liked_recs['track_id'])
        
        num_general = 20 - len(final_track_ids)
        
        general_mood_songs = mood_filtered_songs[~mood_filtered_songs['track_id'].isin(final_track_ids)]
        
        if len(general_mood_songs) > 0:
            num_general = min(len(general_mood_songs), num_general) 
            general_recs = general_mood_songs.sample(n=num_general)
            final_track_ids.extend(list(general_recs['track_id']))
        
        if num_liked > 0:
             message = f"Here are {len(final_track_ids)} songs for you ({num_liked} from your taste, {num_general} new):"
        else:
             message = f"Here are {len(final_track_ids)} songs from our library for you:"
        print(message)
            
        if not final_track_ids:
             return jsonify({'recommendations': [], 'message': 'No songs found.'})

        sp_cc = get_spotify_client_credentials()
        if not sp_cc: return jsonify({'error': 'Could not connect to Spotify for details.'}), 500
        
        recommendations_list = []
        final_songs_df = df_db[df_db['track_id'].isin(final_track_ids)]
        
        for i in range(0, len(final_track_ids), 50):
            batch_ids = final_track_ids[i:i+50]
            try:
                tracks_details = sp_cc.tracks(batch_ids)['tracks']
                for track_detail in tracks_details:
                        if track_detail:
                            db_song = final_songs_df[final_songs_df['track_id'] == track_detail['id']].iloc[0]
                            
                            recommendations_list.append({
                                'id': track_detail['id'], 
                                'name': track_detail.get('name'),
                                'artist': track_detail['artists'][0]['name'] if track_detail.get('artists') else 'N/A',
                                'album_art': track_detail['album']['images'][0]['url'] if track_detail.get('album') and track_detail['album']['images'] else None,
                                'preview_url': track_detail.get('preview_url'), # Keep for script, even if hidden
                                'super_genre': db_song['super_genre'],
                                'url': track_detail['external_urls']['spotify'] if track_detail.get('external_urls') else None
                            })
            except Exception as e:
                print(f"Error getting Spotify track details batch: {e}")

        print(f"Successfully fetched details for {len(recommendations_list)} songs.")
        final_recs_sorted = sorted(recommendations_list, key=lambda x: final_track_ids.index(x['id']))
        
        return jsonify({'recommendations': final_recs_sorted, 'message': message})
    except Exception as e:
        print(f"!! Critical Error in /get_recommendations: {e}"); 
        import traceback; traceback.print_exc()
        return jsonify({'error': 'An internal server error occurred.'}), 500

# --- API: Add ALL Tracks to Playlist ---
@app.route('/add_all_to_playlist', methods=['POST'])
def add_all_to_playlist():
    print("--- Received request at /add_all_to_playlist ---")
    sp_client, needs_redirect = get_spotify_client()
    if needs_redirect: return jsonify({'error': 'User not logged in', 'login_required': True}), 401
    
    data = request.get_json()
    track_ids = data.get('track_ids')
    mood = data.get('mood')
    
    if not track_ids: return jsonify({'error': 'Track IDs not provided'}), 400
    if not mood: return jsonify({'error': 'Mood not provided'}), 400

    playlist_name = f"{mood}: Valora Music Recommendation"
    playlist_id = None
    
    try:
        user_id = sp_client.current_user()['id']
        current_playlists = sp_client.current_user_playlists(limit=50)
        for item in current_playlists.get('items', []):
            if item['name'] == playlist_name: 
                playlist_id = item['id']; 
                print(f"Found existing playlist: {playlist_id}")
                break
                
        if not playlist_id:
            print(f"Creating new playlist: {playlist_name}")
            new_playlist = sp_client.user_playlist_create(user_id, playlist_name, public=False, description="Songs recommended by Valora Music.")
            playlist_id = new_playlist['id']
            
    except Exception as e: return jsonify({'error': f'Could not find/create playlist: {e}'}), 500
    
    if playlist_id:
        try:
            track_uris = [f"spotify:track:{tid}" for tid in track_ids]
            
            # Clear the playlist before adding new songs
            sp_client.playlist_replace_items(playlist_id, []) 
            
            # Add new songs in batches
            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i+100]
                sp_client.playlist_add_items(playlist_id, batch)
                
            return jsonify({'success': True, 'message': f'Added {len(track_uris)} songs to "{playlist_name}"!'})
        except Exception as e:
            return jsonify({'error': f'Could not add songs: {e}'}), 500
    else: return jsonify({'error': 'Playlist ID missing.'}), 500

# --- Run App ---
if __name__ == '__main__':
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        print("ERROR: Please enter your Spotify Client ID and Secret")
    else:
        app.run(debug=True, port=5000)