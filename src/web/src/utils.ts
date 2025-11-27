import $ from 'jquery';

export function notify(message: string): void {
    const notification = $('<div></div>')
        .html(message)
        .css({
            position: 'fixed',
            top: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '10px 20px',
            borderRadius: '5px',
            zIndex: '1000'
        })
        .appendTo('body');

    setTimeout(() => {
        notification.remove();
    }, 4000);
}