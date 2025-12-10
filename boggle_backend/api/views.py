
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Challenge, Games
from .serializers import ChallengeSerializer, GamesSerializer
from .randomGen import *
from .readJSONFile import *
from .boggle_solver import *
from django.contrib.staticfiles import finders
from datetime import datetime
from .services import DictionaryNotFound, generate_valid_words, normalize_grid

# define the endpoints

@api_view(['GET', 'DELETE']) # define a GET Object with pk
def get_game(request, pk):
    try:
        game = Games.objects.get(pk=pk)
    except Games.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = GamesSerializer(game)
        return Response(serializer.data)
    elif request.method == 'DELETE':
        game.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
 
@api_view(['GET']) # define a GET REQUEST to get ALL Games
def get_games(request):
    games = Games.objects.all()
    serializer = GamesSerializer(games, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
def challenges(request):
    if request.method == 'GET':
        all_challenges = Challenge.objects.all()
        serializer = ChallengeSerializer(all_challenges, many=True)
        return Response(serializer.data)

    serializer = ChallengeSerializer(data=request.data)
    if serializer.is_valid():
        challenge = serializer.save()
        return Response(ChallengeSerializer(challenge).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def challenge_detail(request, pk):
    try:
        challenge = Challenge.objects.get(pk=pk)
    except Challenge.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ChallengeSerializer(challenge)
    return Response(serializer.data)


@api_view(['POST'])
def generate_dictionary(request):
    grid = request.data.get('grid')
    if not isinstance(grid, list):
        return Response({"detail": "Grid must be provided as a list of rows."}, status=status.HTTP_400_BAD_REQUEST)

    normalized_grid = normalize_grid(grid)
    grid_size = len(normalized_grid)
    if grid_size not in {4, 5, 6}:
        return Response({"detail": "Grid size must be 4, 5, or 6."}, status=status.HTTP_400_BAD_REQUEST)
    if any(len(row) != grid_size for row in normalized_grid):
        return Response({"detail": f"Grid must be {grid_size}x{grid_size}."}, status=status.HTTP_400_BAD_REQUEST)
    if any(cell == "" for row in normalized_grid for cell in row):
        return Response({"detail": "Grid cells cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        valid_words = generate_valid_words(normalized_grid)
    except DictionaryNotFound as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(
        {"grid_size": grid_size, "valid_words": valid_words},
        status=status.HTTP_200_OK,
    )

@api_view(['GET']) # define a PUT REQUEST TO ADD A SPECIFIC GAME OF SIZE size
def create_game(request, size):
    if not (3 <= size <= 10):
        return Response({"detail": "Size must be between 3 and 10."}, status=status.HTTP_400_BAD_REQUEST)

    g = random_grid(size)
    now = datetime.now()
    name = f'Rand{size}Grid:{now.strftime("%Y-%m-%d %H:%M:%S")}'

    # Find the absolute path of the static JSON file
    file_path = finders.find("data/full-wordlist.json")

    dictionary = read_json_to_list(file_path)
    mygame = Boggle(g, dictionary)
    fwords = mygame.getSolution()

    serializer = GamesSerializer(data={"name": name,"size": size, "grid": str(g), "foundwords": str(fwords)})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
