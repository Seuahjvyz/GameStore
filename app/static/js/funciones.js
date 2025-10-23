
       
        let currentSlide = 0;
        const slides = document.querySelectorAll('.carousel-slide');
        const dots = document.querySelectorAll('.dot');

        function showSlide(index) {
            slides.forEach(slide => slide.classList.remove('active'));
            dots.forEach(dot => dot.classList.remove('active'));
            
            slides[index].classList.add('active');
            dots[index].classList.add('active');
        }

        function nextSlide() {
            currentSlide = (currentSlide + 1) % slides.length;
            showSlide(currentSlide);
        }

        
        setInterval(nextSlide, 5000);

     
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                currentSlide = index;
                showSlide(currentSlide);
            });
        });

        
        const filtros = document.querySelectorAll('.filtro-btn');
        filtros.forEach(filtro => {
            filtro.addEventListener('click', () => {
                filtros.forEach(f => f.classList.remove('active'));
                filtro.classList.add('active');
            });
        });

        
        const botonesAgregar = document.querySelectorAll('.btn-agregar');
        botonesAgregar.forEach(boton => {
            boton.addEventListener('click', (e) => {
                e.stopPropagation();
                boton.textContent = '✓ Agregado';
                boton.style.background = '#8B00FF';
                boton.style.color = '#ffffff';
                
                setTimeout(() => {
                    boton.textContent = 'Agregar';
                    boton.style.background = 'rgba(139, 0, 255, 0.2)';
                    boton.style.color = '#8B00FF';
                }, 2000);
            });
        });