from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from conexion import get_conexion
import os
import psycopg2.errors

#configurar flask 
app = Flask(__name__)
app.secret_key = os.urandom(24)

#ruta principal
@app.route('/', methods= ['GET'])
def index():
    if request.method == 'GET':
        conn = get_conexion()
        if conn is None:
             return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
         
        return render_template('/index.html')




#ruta para crear un pokemon
@app.route('/create_pokemon', methods=['GET', 'POST'])
def create_pokemon():
    if request.method == 'GET':
        # Realizar la conexión
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
        
        try:
            # Consultar habilidades
            cursor = conn.cursor()
            cursor.execute('SELECT id_habilidad, nombre FROM habilidades')
            habilidades = cursor.fetchall()
            
            # Consultar tipos
            cursor.execute('SELECT id_tipo, nombre FROM tipos')
            tipos = cursor.fetchall()
            
            habilidades_list = [{'id_habilidad': h[0], 'nombre': h[1]} for h in habilidades]
            tipos_list = [{'id_tipo': t[0], 'nombre': t[1]} for t in tipos]
            
            return render_template('pokemons/create_pokemon.html', habilidades=habilidades_list, tipos=tipos_list)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        finally:
            cursor.close()
            conn.close()
    
    elif request.method == 'POST':
        # Obtener los datos del formulario
        data = request.form
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos en el formulario'}), 400
        
        required_fields = ['nombre', 'hp', 'ataque', 'defensa', 'ataque_especial', 'defensa_especial', 'id_tipo', 'id_habilidad']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({'error': f'Faltan datos necesarios: {", ".join(missing_fields)}'})
        
        nombre = data.get('nombre')
        hp = data.get('hp')
        ataque = data.get('ataque')
        defensa = data.get('defensa')
        ataque_especial = data.get('ataque_especial')
        defensa_especial = data.get('defensa_especial')
        id_tipo = data.get('id_tipo')
        id_habilidad = data.get('id_habilidad')
        
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
        
        try:
            cursor = conn.cursor()
            query = '''INSERT INTO pokemon (nombre, hp, ataque, defensa, ataque_especial, defensa_especial, 
            id_tipo, id_habilidad) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_pokemon'''
            cursor.execute(query, (nombre, hp, ataque, defensa, ataque_especial, defensa_especial, id_tipo, id_habilidad))
            new_id = cursor.fetchone()[0]
            conn.commit()
            
            flash('Pokemon creado con éxito')
            return redirect(url_for('create_pokemon'))
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        finally:
            cursor.close()
            conn.close()




#ruta para visualizar todos los pokemones
@app.route('/view_pokemon', methods=['GET'])
def view_pokemon():
    conn = None
    try:
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
        
        cursor = conn.cursor()
        query = '''
        SELECT p.id_pokemon, p.nombre, p.hp, p.ataque, p.defensa, p.ataque_especial, p.defensa_especial, 
                t.nombre AS tipo_nombre, h.nombre AS habilidad_nombre
        FROM pokemon p
        JOIN tipos t ON p.id_tipo = t.id_tipo
        JOIN habilidades h ON p.id_habilidad = h.id_habilidad;
        '''
        cursor.execute(query)
        pokemones = cursor.fetchall()

        # Convertir los resultados a una lista de diccionarios
        pokemones_list = [
            {
                'id_pokemon': p[0],
                'nombre': p[1],
                'hp': p[2],
                'ataque': p[3],
                'defensa': p[4],
                'ataque_especial': p[5],
                'defensa_especial': p[6],
                'tipo_nombre': p[7],
                'habilidad_nombre': p[8]
            }
            for p in pokemones
        ]
        
        return render_template('pokemons/view_pokemon.html', pokemones=pokemones_list)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Asegurarse de cerrar la conexión, si está abierta
        if conn is not None and not conn.closed:
            conn.close()


    
#ruta para actualizar pokemones
@app.route('/update_pokemon/<int:id_pokemon>/update', methods=['GET', 'POST'])
def update_pokemon(id_pokemon):
    if request.method == 'POST':
        data = request.form
        
        # Obtener todos los datos del formulario
        nombre = data.get('nombre')
        hp = data.get('hp')
        ataque = data.get('ataque')
        defensa = data.get('defensa')
        ataque_especial = data.get('ataque_especial')
        defensa_especial = data.get('defensa_especial')
            
        try:
            id_tipo = int(data.get('id_tipo'))
            id_habilidad = int(data.get('id_habilidad'))
        except ValueError:
            return jsonify({'error': 'El valor de id_tipo o id_habilidad no es válido'}), 400
        
        # Verificar que el formulario no se envíe vacío
        if not data:
            return jsonify({'error': 'No se proporcionaron datos en el formulario'}), 400
        
        
        # Realizar la conexión
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

        # Try except que maneja la query para actualizar los datos del Pokémon
        
        try:
            cursor = conn.cursor()
            query =  ('''UPDATE public.pokemon
                SET nombre= %s, hp= %s, ataque=%s, defensa=%s, ataque_especial=%s, 
                    defensa_especial=%s, 
                    id_tipo=%s, id_habilidad=%s
                WHERE id_pokemon = %s;''')
            cursor.execute(query, (nombre, hp, ataque, defensa, ataque_especial, defensa_especial, id_tipo, id_habilidad, id_pokemon))
            conn.commit()
            
             # Redirige a la página de visualización
            return redirect(url_for('view_pokemon', id_pokemon=id_pokemon))
        
        except Exception as e:
            return jsonify ({'error' : str(e)}), 500
        finally:
                cursor.close()
                conn.close()
            
    elif request.method == 'GET':
        
        conn = get_conexion()
        
        if conn is None:
            return jsonify({'error': 'no se pudo conectar a la base de datos'}), 500
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pokemon WHERE id_pokemon = %s',  (id_pokemon,))
            pokemon = cursor.fetchone()
            
            if pokemon is None:
                return jsonify({'error' : 'no se encontro el pokemon'}), 404
            
            # Convertir la tupla a un diccionario para facilitar el acceso en la plantilla
            pokemon_dict = {
                'id_pokemon': pokemon[0],
                'nombre': pokemon[1],
                'hp': pokemon[2],
                'ataque': pokemon[3],
                'defensa': pokemon[4],
                'ataque_especial': pokemon[5],
                'defensa_especial': pokemon[6],
                'id_tipo': pokemon[7],
                'id_habilidad': pokemon[8]
            }
            query_habilidades = 'SELECT id_habilidad, nombre FROM habilidades'
            cursor.execute(query_habilidades)
            habilidades = cursor.fetchall()
            
            
            query_tipos = 'SELECT id_tipo, nombre FROM tipos'
            cursor.execute(query_tipos)
            tipos = cursor.fetchall()
            
               # Imprimir los datos para verificar
            print("Habilidades:", habilidades)
            print("Tipos:", tipos)
            return render_template('pokemons/update_pokemon.html', pokemon=pokemon_dict, habilidades = habilidades, tipos = tipos)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        finally:
            cursor.close()
            conn.close()
            
            
            
#ruta de eliminar pokemones            
@app.route('/delete_pokemon', methods=['POST'])
def delete_pokemon():
    data = request.form
    id_pokemon = data.get('id_pokemon')
    
    if not id_pokemon:
        return jsonify({'error': 'ID del Pokémon no proporcionado'}), 400

    # Realizar la conexión
    conn = get_conexion()
    if conn is None:
        return jsonify({'error': 'No se pudo realizar la conexión a la base de datos'}), 500
    
    cursor = None
    try:
        cursor = conn.cursor()
        # Usar formato de parámetros adecuado para PostgreSQL
        cursor.execute('DELETE FROM pokemon WHERE id_pokemon = %s', (id_pokemon,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Pokémon no encontrado'}), 404

        return redirect(url_for('view_pokemon'))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




#ruta para ver todas las habilidades
@app.route('/habilidades_pokemon', methods = ['GET'])
def view_habilidades_pokemon():
    conn = get_conexion()
    if conn is None:
        return jsonify ({'error': 'no se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id_habilidad, nombre FROM habilidades')
        habilidades = cursor.fetchall() 
        
        habilidades_list = [{'id_habilidad': h[0], 'nombre': h[1]} for h in habilidades]
        return render_template('pokemons/create_pokemon.html', habilidades=habilidades_list)
    
    except Exception as e:
        return jsonify({'error' : str(e)}), 500
    
    finally:
            cursor.close()
            conn.close()




#ruta para ver todos los tipos de pokemon
@app.route('/tipos_pokemon', methods = ['GET'])
def view_tipos_pokemon():
    conn = get_conexion()
    if conn is None:
        return jsonify ({'error': 'no se pudo conectar a la base de datos'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id_tipo, nombre FROM tipos')
        tipos = cursor.fetchall()
        
        tipos_list = [{'id_tipo': h[0], 'nombre': h[1]} for h in tipos]
        return render_template('pokemons/create_pokemon.html', tipos=tipos_list)
    
    except Exception as e:
        return jsonify({'error' : str(e)}), 500
    
    finally:
            cursor.close()
            conn.close()



#ruta de crear un entrenador
@app.route('/create_trainner', methods=['GET', 'POST'])
def create_trainner():
    if request.method == 'GET':
        #renderizar 
        return render_template('trainners/create_trainner.html')

    elif request.method == 'POST':
        # Obtener los datos del formulario
        data = request.form
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos en el formulario'}), 400
        
        required_fields = ['nombre', 'ciudad_origen', 'region', 'rango', 'genero', 'edad']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({'error': f'Faltan datos necesarios: {", ".join(missing_fields)}'})
        
        nombre = data.get('nombre')
        ciudad_origen = data.get('ciudad_origen')
        region = data.get('region')
        rango = data.get('rango')
        genero = data.get('genero')
        edad = data.get('edad')
      
        
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
        
        try:
            cursor = conn.cursor()
            query = '''INSERT INTO public.entrenador(
            nombre, ciudad_origen, region, rango, genero, 
            edad) VALUES (%s, %s, %s, %s, %s, %s)RETURNING id_entrenador'''
            cursor.execute(query, (nombre, ciudad_origen, region, rango, genero, edad ))
            new_id = cursor.fetchone()[0]
            conn.commit()
            
            flash('Entrenador creado con éxito')
            # Redirigir a la misma página para vaciar el formulario
            return redirect(url_for('create_trainner'))
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        finally:
            cursor.close()
            conn.close()
    


#ruta para eliminar un entrenador            
@app.route('/delete_trainner', methods=['POST'])
def delete_trainner():
    data = request.form
    id_entrenador = data.get('id_entrenador')
    
    if not id_entrenador:
        return jsonify({'error': 'ID del Entrenador no proporcionado'}), 400

    # Realizar la conexión
    conn = get_conexion()
    if conn is None:
        return jsonify({'error': 'No se pudo realizar la conexión a la base de datos'}), 500
    
    cursor = None
    try:
        cursor = conn.cursor()
        # Usar formato de parámetros adecuado para PostgreSQL
        cursor.execute('DELETE FROM entrenador WHERE id_entrenador = %s', (id_entrenador,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Entrenador no encontrado'}), 404

        return redirect(url_for('view_trainners'))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


#ruta para asignar pokemones a entrenadores
@app.route('/assign_pokemon_to_trainer', methods=['GET', 'POST'])
def assign_pokemon_to_trainer():
    if request.method == 'POST':
        data = request.form

        if not data:
            flash('No se proporcionaron datos en el formulario', 'error')
            return redirect(url_for('assign_pokemon_to_trainer'))

        id_entrenador = data.get('id_entrenador')
        id_pokemon = data.get('id_pokemon')

        conn = get_conexion()
        if conn is None:
            flash('No se pudo conectar a la base de datos', 'error')
            return redirect(url_for('assign_pokemon_to_trainer'))

        try:
            cursor = conn.cursor()

            # Verificar si el Pokémon ya está asignado a otro entrenador
            query_check = '''SELECT * FROM public.pokemon_entrenador 
                             WHERE id_pokemon = %s'''
            cursor.execute(query_check, (id_pokemon,))
            if cursor.fetchone():
                flash('El Pokémon ya está asignado a otro entrenador', 'error')
                return redirect(url_for('assign_pokemon_to_trainer'))

            # Crear la relación entre entrenador y pokemon
            query_relation = '''INSERT INTO public.pokemon_entrenador(id_entrenador, id_pokemon)
                                VALUES (%s, %s)'''
            cursor.execute(query_relation, (id_entrenador, id_pokemon))
            conn.commit()

            flash('Pokémon asignado al entrenador exitosamente', 'message')
            return redirect(url_for('assign_pokemon_to_trainer'))

        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('El Pokémon ya está asignado a este entrenador', 'error')
            return redirect(url_for('assign_pokemon_to_trainer'))

        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('assign_pokemon_to_trainer'))

        finally:
            cursor.close()
            conn.close()

    else:  # Método GET
        conn = get_conexion()
        if conn is None:
            flash('No se pudo conectar a la base de datos', 'error')
            return redirect(url_for('assign_pokemon_to_trainer'))

        try:
            cursor = conn.cursor()

            # Obtener todos los entrenadores
            query_entrenador = '''SELECT id_entrenador, nombre FROM public.entrenador'''
            cursor.execute(query_entrenador)
            entrenador = cursor.fetchall()

            # Obtener todos los Pokémon
            query_pokemons = '''SELECT id_pokemon, nombre FROM public.pokemon'''
            cursor.execute(query_pokemons)
            pokemon = cursor.fetchall()

            # Convertir los datos a listas de diccionarios
            entrenador = [{'id_entrenador': e[0], 'nombre': e[1]} for e in entrenador]
            pokemon = [{'id_pokemon': p[0], 'nombre': p[1]} for p in pokemon]

            return render_template('batallas/assign_pokemon_to_trainer.html', entrenador=entrenador, pokemon=pokemon)

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('assign_pokemon_to_trainer'))

        finally:
            cursor.close()
            conn.close()
#ruta para ver entrenadores con sus pokemones
@app.route('/view_trainner_pokemon', methods=['GET'])
def view_trainner_pokemon():
    conn = None
    try:
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
        
        cursor = conn.cursor()
        query = '''SELECT e.id_entrenador AS id_entrenador, e.nombre AS entrenador_nombre, 
        p.id_pokemon AS id_pokemon, p.nombre AS pokemon_nombre
        FROM pokemon_entrenador pt
        JOIN entrenador e ON pt.id_entrenador = e.id_entrenador
        JOIN pokemon p ON pt.id_pokemon = p.id_pokemon;
        '''
        cursor.execute(query)
        pokemon_trainner = cursor.fetchall()

        # Convertir los resultados a una lista de diccionarios
        pokemon_trainner_list = [
            {
                'id_entrenador': pt[0],
                'entrenador_nombre': pt[1],
                'id_pokemon': pt[2],
                'pokemon_nombre': pt[3]
            }
            for pt in pokemon_trainner
        ]
        
        return render_template('view_trainner_pokemon.html', pokemon_trainner=pokemon_trainner_list)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Asegurarse de cerrar la conexión, si está abierta
        if conn is not None and not conn.closed:
            conn.close()


    
#ruta para crear una nueva batalla
@app.route('/create_battle', methods=['GET', 'POST'])
def create_battle():
    if request.method == 'GET':
        # Realizar la conexión
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id_entrenador, nombre FROM entrenador')
            trainners = cursor.fetchall()
            cursor.close()
            conn.close()

            return render_template('batallas/create_battle.html', trainners=trainners)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if conn:
                conn.close()
    
    elif request.method == 'POST':
        data = request.form
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos en el formulario'}), 400
        
        fecha_batalla = data.get('fecha_batalla')
        hora_batalla = data.get('hora_batalla')
        duracion_batalla = data.get('duracion_batalla')
        lugar_batalla = data.get('lugar_batalla')
        
        try:
            entrenador_1 = int(data.get('entrenador_1'))
            entrenador_2 = int(data.get('entrenador_2'))
           
            # Verificar que los entrenadores no sean iguales
            if entrenador_1 == entrenador_2:
                return jsonify({'error': 'Los entrenadores no pueden ser iguales'}), 400
            
        except ValueError:
            return jsonify({'error': 'El valor de entrenador_1 o entrenador_2 no es válido'}), 400
        
        # Almacenar temporalmente los datos de la batalla y los entrenadores seleccionados
        session['batalla'] = {
            'fecha_batalla': fecha_batalla,
            'hora_batalla': hora_batalla,
            'duracion_batalla': duracion_batalla,
            'lugar_batalla': lugar_batalla,
            'entrenador_1': entrenador_1,
            'entrenador_2': entrenador_2
        }
        
        return redirect(url_for('select_winner'))
       


#ruta para seleccionar ganador
@app.route('/select_winner', methods=['GET', 'POST'])
def select_winner():
    if request.method == 'GET':
            batalla_data = session.get('batalla')
            if not batalla_data:
                return jsonify({'error': 'No se encontraron datos de la batalla'})

            conn = get_conexion()
            if conn is None:
                return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

            try:
                cursor = conn.cursor()
                cursor.execute('SELECT id_entrenador, nombre FROM entrenador WHERE id_entrenador IN (%s, %s)', 
                            (batalla_data['entrenador_1'], batalla_data['entrenador_2']))
                trainners = cursor.fetchall()
                cursor.close()
                conn.close()
                
                return render_template('batallas/select_winner.html', trainners=trainners)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                if conn:
                    conn.close()
    
    elif request.method == 'POST':
        data = request.form
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos en el formulario'}), 400
        
        try:
            entrenador_ganador_id = int(data.get('entrenador_ganador_id'))
            entrenador_perdedor_id = int(data.get('entrenador_perdedor_id'))
             # Verificar que los ganadores y perdedores sean diferentes
            if entrenador_ganador_id == entrenador_perdedor_id:
                return jsonify({'error': 'El ganador y el perdedor no pueden ser iguales'}), 400
        
        except ValueError:
            return jsonify({'error': 'El valor de entrenador_ganador_id o entrenador_perdedor_id no es válido'}), 400
        
        batalla_data = session.get('batalla')
        
        if not batalla_data:
            return jsonify({'error': 'No se encontraron datos de batalla'}), 400
        
        # Insertar los datos de la batalla en la base de datos
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
        
        
        try:
            cursor = conn.cursor()
            query = '''
                INSERT INTO batallas (fecha_batalla, hora_batalla, entrenador_1, entrenador_2, duracion_batalla, 
                                      entrenador_ganador_id, entrenador_perdedor_id, empate, lugar_batalla) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_batalla;'''
            cursor.execute(query, (batalla_data['fecha_batalla'], batalla_data['hora_batalla'], batalla_data['entrenador_1'],
                                   batalla_data['entrenador_2'], batalla_data['duracion_batalla'], entrenador_ganador_id, 
                                   entrenador_perdedor_id, False, batalla_data['lugar_batalla']))
            new_id = cursor.fetchone()[0]
            conn.commit()
            
            session.pop('batalla', None)
            
            flash('Batalla creada con éxito')
            return redirect(url_for('create_battle'))
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        finally:
            cursor.close()
            conn.close()



#ruta para eliminar una batalla
@app.route('/delete_battle', methods=['POST'])
def delete_battle():
    data = request.form
    id_batalla = data.get('id_batalla')
    
    if not id_batalla:
        return jsonify({'error': 'ID de la batalla no proporcionada'}), 400

    # Realizar la conexión
    conn = get_conexion()
    if conn is None:
        return jsonify({'error': 'No se pudo realizar la conexión a la base de datos'}), 500
    
    cursor = None
    try:
        cursor = conn.cursor()
        # Usar formato de parámetros adecuado para PostgreSQL
        cursor.execute('DELETE FROM batallas WHERE id_batalla = %s', (id_batalla,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'error': 'Batalla no encontrada'}), 404

        return redirect(url_for('view_battle'))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
   
#ruta para ver todas las batallas  
@app.route('/view_battle', methods=['GET'])
def view_battle():
    conn = None
    try:
        conn = get_conexion()
        if conn is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500
        
        cursor = conn.cursor()
        query = ''' SELECT 
                b.id_batalla, 
                b.fecha_batalla, 
                b.hora_batalla, 
                e1.nombre AS entrenador_1_nombre, 
                p1.nombre AS pokemon_entrenador_1, 
                e2.nombre AS entrenador_2_nombre, 
                p2.nombre AS pokemon_entrenador_2, 
                b.duracion_batalla, 
                e3.nombre AS entrenador_ganador_nombre, 
                e4.nombre AS entrenador_perdedor_nombre,
                b.lugar_batalla
               
            FROM batallas b
            LEFT JOIN 
                entrenador e1 ON b.entrenador_1 = e1.id_entrenador
            LEFT JOIN 
                pokemon_entrenador ep1 ON e1.id_entrenador = ep1.id_entrenador
            LEFT JOIN 
                pokemon p1 ON ep1.id_pokemon = p1.id_pokemon
            LEFT JOIN 
                entrenador e2 ON b.entrenador_2 = e2.id_entrenador
            LEFT JOIN 
                pokemon_entrenador ep2 ON e2.id_entrenador = ep2.id_entrenador
            LEFT JOIN 
                pokemon p2 ON ep2.id_pokemon = p2.id_pokemon
            LEFT JOIN 
                entrenador e3 ON b.entrenador_ganador_id = e3.id_entrenador
            LEFT JOIN 
                entrenador e4 ON b.entrenador_perdedor_id = e4.id_entrenador; '''
        cursor.execute(query)
        batalla_view = cursor.fetchall()

        # Convertir los resultados a una lista de diccionarios
        batalla_list = [
            {
                'id_batalla': b[0],
                'fecha_batalla': b[1],
                'hora_batalla': b[2],
                'entrenador_1_nombre': b[3],
                'pokemon_entrenador_1': b[4],
                'entrenador_2_nombre': b[5],
                'pokemon_entrenador_2': b[6],
                'duracion_batalla': b[7],
                'entrenador_ganador_nombre': b[8],
                'entrenador_perdedor_nombre': b[9],
                'lugar_batalla' : b[10]
                
            }
            for b in batalla_view
        ]
        
        return render_template('batallas/view_battle.html', batalla_view=batalla_list)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Asegurarse de cerrar la conexión, si está abierta
        if conn is not None and not conn.closed:
            conn.close()

#verifica que el bloque de codigo se ejecute solo cuando es ejecutado directamente 
if __name__ == '__main__': #si el archivo es importado desde otro modulo, name cambiara de valor
    app.run(debug=True)