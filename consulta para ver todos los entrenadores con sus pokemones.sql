SELECT pe.id, e.id_entrenador, p.id_pokemon, e.nombre AS entrenador_nombre, p.nombre AS pokemon_nombre
  FROM public.pokemon_entrenador pe
  JOIN entrenador e ON pe.id_entrenador = e.id_entrenador
  JOIN pokemon p ON pe.id_pokemon = p.id_pokemon
  ;
